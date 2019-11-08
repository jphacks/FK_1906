import sys
import time
import math
import cv2
import json
import base64
import requests
import numpy
import threading
import queue
import numpy as np

import os
import io
# request フォームから送信した情報を扱うためのモジュール
# redirect  ページの移動
# url_for アドレス遷移
from flask import Flask, request, redirect, url_for, render_template, jsonify
# ファイル名をチェックする関数
from werkzeug.utils import secure_filename
# 画像のダウンロード
from flask import send_from_directory

from api import videoReader
from sound import analyze_sound
import matplotlib.pyplot as plt

import moviepy.editor as mp

from models.models import Progress
from models.database import db_session
app = Flask(__name__)

# 学習済みモデルのロード
import pickle

models = {}
for filename in os.listdir('data'):
    label = filename.split('.')[0]
    models[label] = pickle.load(open(os.path.join('data', filename), 'rb'))


# 画像のアップロード先のディレクトリ
UPLOAD_FOLDER = './uploads'
# アップロードされる拡張子の制限
ALLOWED_EXTENSIONS = set(['mp4'])

def digitize_score(target, begin, end, digits=5):
    return np.digitize(target, bins=np.linspace(begin, end, digits+1)[1:-1])


def allwed_file(filename):
    # .があるかどうかのチェックと、拡張子の確認
    # OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def set_progress_data(frames, progress):
    progress_data = Progress.query.first()
    progress_data.movie_frames = frames
    progress_data.movie_progress = progress
    db_session.add(progress_data)
    db_session.commit()

def user_pich_image(pich_mean_score):
    image_path = "/static/images/"
    if(pich_mean_score > 20):
        image_path += "top.png"
    elif(pich_mean_score > 10):
        image_path += "middle.png"
    elif(pich_mean_score >= 0):
        image_path += "buttom.png"

    return image_path

# ファイルを受け取る方法の指定
@app.route('/', methods=['GET', 'POST'])
def uploads_file():
    now_loading = True
    if request.method == "POST":
        if 'file' not in request.files:
            print("ファイルがありません")
        else:
            img = request.files["file"]
            filename = secure_filename(img.filename)

            root, ext = os.path.splitext(filename)
            ext = ext.lower()

            gazouketori = set([".mp4"])
            if ext not in gazouketori:
                return render_template('index.html',massege = "対応してない拡張子です",color = "red")
            print("success")
            try:
                ### Main ######################################################################
                file = request.files['file']
                videoSource = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
                file.save(videoSource)
                print("videonSouse", videoSource)
                print("app",app.config['UPLOAD_FOLDER'])
                sound_analize_result = analyze_sound(videoSource)

                # Extract audio from input video.
                clip_input = mp.VideoFileClip(videoSource).subclip()
                clip_input.audio.write_audiofile('audio.mp3')

                gaze_list = videoReader(videoSource)

                set_progress_data(-1, -1) #progress go to write video
                
                editedVideoSource = os.path.join(app.config['UPLOAD_FOLDER'], "edited.avi")

                # Add audio to output video.
                clip_output = mp.VideoFileClip(editedVideoSource).subclip()


                clip_output.write_videofile(editedVideoSource.replace('.avi', '.mp4'), audio='audio.mp3')

                set_progress_data(0, 0) #progress go to finish and database reset

                yaw_list, pich_list = zip(*gaze_list)
                yaw_list, pich_list = np.array(yaw_list), np.array(pich_list)
                yaw_mean,  yaw_var  = np.mean(yaw_list),  np.var(yaw_list)
                pich_mean, pich_var = np.mean(pich_list), np.var(pich_list)

                print("[yaw] mean: {}, var: {}".format(yaw_mean, yaw_var))
                print("[pich] mean: {}, var: {}".format(pich_mean, pich_var))

                center_range = np.array([-10, 10])
                LEFT   = 0
                CENTER = 1
                RIGHT  = 2
                yaw_distribution = {LEFT: 0, CENTER: 0, RIGHT: 0}
                for yaw in yaw_list:
                    pos = np.digitize(yaw, bins=center_range)
                    yaw_distribution[pos] += 1

                num_total = float(len(yaw_list))
                left_rate   = yaw_distribution[LEFT]   / num_total
                center_rate = yaw_distribution[CENTER] / num_total
                right_rate  = yaw_distribution[RIGHT]  / num_total
                print("left: {}, center: {}, right: {}".format(left_rate, center_rate, right_rate))

                img = io.BytesIO()
                plt.hist(yaw_list, bins=50)
                plt.savefig(img, format='png')
                # img.seek(0)

                plot_b64str = base64.b64encode(img.getvalue()).decode("utf-8")
                plot_b64data = "data:image/png;base64,{}".format(plot_b64str)
                plt.clf()

                amp_mean = sound_analize_result["volume_mean"]
                amp_var = sound_analize_result["volume_var"]
                fle_var = sound_analize_result["tone_var"]


                # スコアの計算
                # ヒューリスティック ver
                yaw_mean_score  = digitize_score(yaw_mean,  0.3, 0.8)
                yaw_var_score   = digitize_score(yaw_var,   30,  10)
                pich_mean_score = digitize_score(pich_mean, 20,  10)
                amp_var_score   = digitize_score(amp_var,   5,   10)
                fle_var_score   = digitize_score(fle_var,   10,  20)

                gaze_score = sum((yaw_mean_score, yaw_var_score, pich_mean_score)) * 5
                intonation_score = sum((amp_var_score, fle_var_score) * 5)

                # 機械学習 ver
                yaw_var     = yaw_var.reshape(-1, 1)
                pich_mean   = pich_mean.reshape(-1, 1)
                volume_mean = amp_mean.reshape(-1, 1) # Renaming
                tone_var    = fle_var.reshape(-1, 1) # Renaming

                yaw_var_score = int(models['yaw_var_score'].predict(yaw_var)*0.2)
                pich_mean_score = int(models['pich_mean_score'].predict(pich_mean)*0.3)
                volume_mean_score = int(models['volume_mean_score'].predict(volume_mean)*0.3)
                tone_var_score = int(models['tone_var_score'].predict(tone_var)*0.2)

                total_score = yaw_var_score + pich_mean_score + volume_mean_score + tone_var_score

                print("yaw_var_score: ",     yaw_var_score)
                print("pich_mean_score: ",   pich_mean_score)
                print("volume_mean_score: ", volume_mean_score)
                print("tone_var_score: ",    tone_var_score)
                print("[total_score]: ", total_score)

                #Image Path の指定
                pich_image_path = user_pich_image(pich_mean_score)

                kwargs = {
                    "predicted"  : True,
                    "yaw_mean"   : yaw_mean,
                    "yaw_var"    : yaw_var,
                    "pich_mean"  : pich_mean,
                    "pich_var"   : pich_var,
                    "left_rate"  : left_rate,
                    "center_rate": center_rate,
                    "right_rate" : right_rate,
                    "amp_mean"   : amp_mean,
                    "amp_var"    : amp_var,
                    "fle_var"    : fle_var,
                    "yaw_mean_score": yaw_mean_score,
                    "yaw_var_score": yaw_var_score,
                    "pich_mean_score": pich_mean_score,
                    "amp_var_score": amp_var_score,
                    "fle_var_score": fle_var_score,
                    "gaze_score" : gaze_score,
                    "intonation_score": intonation_score,
                    "plot_url"   : plot_b64data,
                    "total_score": total_score,
                    "volume_mean_score": volume_mean_score,
                    "tone_var_score": tone_var_score,
                    "pich_image_path": pich_image_path
                }
                params_for_train = {
                    "yaw_var"    : yaw_var,   # 目線の左右の分散
                    "pich_mean"  : pich_mean, # 目線の高さの平均
                    "volume_mean": amp_mean,  # 声の大小の平均
                    "tone_var"   : fle_var    # 声のトーンの分散
                }

                now_loading = False
                write_analysis_result(filename, params_for_train)
                return render_template("index.html", now_loading=now_loading, **kwargs)

            except Exception as e:
                print(e)
                return render_template('index.html',massege = "解析出来ませんでした",color = "red")

    else:
        print("get request")
        return render_template('index.html', now_loading=now_loading)

def write_analysis_result(filepath, results):
    filename = os.path.basename(filepath)
    with open(os.path.join("./results", filename+".txt"), mode='w') as f:
        for key, value in results.items():
            result_str = "{}:{}\n".format(key, value)
            f.write(result_str)


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/progress",methods=["post"])
def progress():

    progress = Progress.query.first()
    text = ""
    if progress is None:
        text = "処理中"

    elif progress.movie_frames <= 0 and progress.movie_progress <= 0:
        status = progress.movie_frames

        if status == 0:
            text = ""
        elif status == -1:
            text = "動画保存中"

    else :
        text = str(progress.movie_progress) + "/" + str(progress.movie_frames)

    return jsonify({'text' : text})

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

import subprocess

def analyze_localy(dirname):
    video_files = [os.path.join(dirname, video_filename) for video_filename in os.listdir(dirname)]
    for filename in video_files:
        sound_analize_result = analyze_sound(filename)
        gaze_list = videoReader(filename)
        yaw_list, pich_list = zip(*gaze_list)
        yaw_list, pich_list = np.array(yaw_list), np.array(pich_list)

        yaw_mean,  yaw_var  = np.mean(yaw_list),  np.var(yaw_list)
        pich_mean, pich_var = np.mean(pich_list), np.var(pich_list)
        amp_mean = sound_analize_result["volume_mean"]
        fle_var = sound_analize_result["tone_var"]

        params_for_train = {
            "yaw_var"    : yaw_var,   # 目線の左右の分散
            "pich_mean"  : pich_mean, # 目線の高さの平均
            "volume_mean": amp_mean,  # 声の大小の平均
            "tone_var"   : fle_var    # 声のトーンの分散
        }
        write_analysis_result(filename, params_for_train)
        basename = os.path.basename(filename)
        subprocess.run(['mv', 'uploads/edited.avi', 'uploads/edited_'+basename+'.avi'])


if __name__ == '__main__':
    app.run()
