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

import os
import io
# request フォームから送信した情報を扱うためのモジュール
# redirect  ページの移動
# url_for アドレス遷移
from flask import Flask, request, redirect, url_for, render_template
# ファイル名をチェックする関数
from werkzeug.utils import secure_filename
# 画像のダウンロード
from flask import send_from_directory

from api import videoReader



app = Flask(__name__)

# 画像のアップロード先のディレクトリ
UPLOAD_FOLDER = './uploads'
# アップロードされる拡張子の制限
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'gif', 'mp4'])

def allwed_file(filename):
    # .があるかどうかのチェックと、拡張子の確認
    # OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ファイルを受け取る方法の指定
@app.route('/', methods=['GET', 'POST'])
def uploads_file():
    # # リクエストがポストかどうかの判別
    # if request.method == 'POST':
    #     # ファイルがなかった場合の処理
    #     if 'file' not in request.files:
    #         flash('ファイルがありません')
    #         return redirect(request.url)
    #     # データの取り出し
    #     file = request.files['file']
    #     # ファイル名がなかった時の処理
    #     if file.filename == '':
    #         flash('ファイルがありません')
    #         return redirect(request.url)
    #     # ファイルのチェック
    #     if file and allwed_file(file.filename):
    #         # 危険な文字を削除（サニタイズ処理）
    #         filename = secure_filename(file.filename)
    #         # ファイルの保存
    #         file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    #         # アップロード後のページに転送
    #         return redirect(url_for('uploaded_file', filename=filename))
    return render_template('index.html')


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/predict', methods=['GET','POST'])
def predict():
    if request.method == "POST":
        if 'file' not in request.files:
            print("ファイルがありません")
        else:
            img = request.files["file"]
            filename = secure_filename(img.filename)

            root, ext = os.path.splitext(filename)
            ext = ext.lower()

            gazouketori = set([".jpg", ".jpeg", ".jpe", ".jp2", ".png", ".webp", ".bmp", ".pbm", ".pgm", ".ppm",
                               ".pxm", ".pnm",  ".sr",  ".ras", ".tiff", ".tif", ".exr", ".hdr", ".pic", ".dib", ".mp4"])
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
                videoReader(videoSource)

            except:
                return render_template('index.html',massege = "解析出来ませんでした",color = "red")

            #  buf = io.BytesIO()
            #  image = Image.open(img)
            #  image.save(buf, 'png')
            #  qr_b64str = base64.b64encode(buf.getvalue()).decode("utf-8")
            #  qr_b64data = "data:image/png;base64,{}".format(qr_b64str)

            return render_template("index.html")
            #  return render_template('index.html', img=qr_b64data, pre1_img_url=pre1_img_url, pre1_detail=pre1_detail, pre1_pro=pre1_pro, pre2_img_url=pre2_img_url, pre2_detail=pre2_detail, pre2_pro=pre2_pro, pre3_img_url=pre3_img_url, pre3_detail=pre3_detail, pre3_pro=pre3_pro)
    else:
        print("get request")

    return render_template('index.html')




@app.route('/uploads/<filename>')
# ファイルを表示する
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run()
