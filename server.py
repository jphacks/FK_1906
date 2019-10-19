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
# request フォームから送信した情報を扱うためのモジュール
# redirect  ページの移動
# url_for アドレス遷移
from flask import Flask, request, redirect, url_for, render_template
# ファイル名をチェックする関数
from werkzeug.utils import secure_filename
# 画像のダウンロード
from flask import send_from_directory

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
                __author__  = "Yoshi Kajiki <y-kajiki@ah.jp.nec.com>"
                __version__ = "0.9"
                __date__    = "Oct 18, 2019"

                endPoint = 'http://a8b88762ef01211e9950f0eacce6e863-2021028779.ap-northeast-1.elb.amazonaws.com'       # for JPHACKS 2019

                proxies = []
                #proxies = ['http':'http://proxygate2.nic.nec.co.jp:8080', 'https':'http://proxygate2.nic.nec.co.jp:8080']

                displayFlag = True
                #displayFlag = False

                ###############################################################################
                # Send Request
                def sendRequest(image, width, height):
                    global resultQueue
                    global proxies

                    # Extrace RAW image
                    imgGray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    imgRawArray = numpy.reshape(imgGray, (-1))
                    imgRaw = imgRawArray.tobytes()

                    # Set URL
                    url = endPoint + "/v1/query/gaze_byRAW"

                    # Set request parameter
                    reqPara = {
                        'width' : width,
                        'height' : height,
                        'raw_b64' : base64.b64encode(imgRaw).decode('utf-8')
                    }
                    params = {
                        'smooth' : 'yes',
                    }

                    # Send the request
                    headers = {'Content-Type' : 'application/json'}
                    data = json.dumps(reqPara).encode('utf-8')
                    try:
                        res = requests.post(url, params=params, data=data, headers=headers, proxies=proxies, timeout=5)
                    except:
                        print('Error! Can not connect to the API.')
                        #return []
                        sys.exit(1)

                    # Get response
                    if res.status_code == 200:
                        # print(json.dumps(res.json(), indent=4))
                        #resultQueue.put(res.json())
                        return res.json()
                    else:
                        print('## Error! ##')
                        print(res.text)
                        return []

                def videoReader(videoSource):

                    # Open the Video
                    try:
                        video = cv2.VideoCapture(videoSource)
                    except:
                        print('Error!  Can not open the video [%s].' % videoSource)
                        sys.exit(1)
                    if not video.isOpened():
                        print('Error!  Can not open the video [%s].' % videoSource)
                        sys.exit(1)

                    # Read Parameters of the Video
                    width = video.get(cv2.CAP_PROP_FRAME_WIDTH)
                    height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    fps = video.get(cv2.CAP_PROP_FPS)
                    interval = 1. / fps
                    results = []
                    eyesColor = (255, 0, 0)
                    gaze = None
                    gazeLen = width / 5
                    gazeColor = (0, 255, 0)

                    # Create video writer
                    fourcc = cv2.VideoWriter_fourcc('M', 'P', '4', 'V')
                    writer = cv2.VideoWriter('./uploads/edited.mp4', fourcc, fps, (int(width), int(height)))

                    # Read the Video Stream
                    while True:

                        # Read a frame
                        success, image = video.read()
                        stTime = time.time()
                        while not success:
                            video.release()
                            cv2.destroyAllWindows()
                            writer.release()
                            return
                        frameNo = video.get(cv2.CAP_PROP_POS_FRAMES)

                        # call API with frameRateAPI
                        results = sendRequest(image, width, height)

                        #######################################################################
                        # Edit for your application
                        #######################################################################
                        for result in results:
                            reye = result['reye']
                            leye = result['leye']
                            gaze = result['gaze']

                            cv2.circle(image, (int(reye[0]), int(reye[1])), 15, eyesColor, thickness=2)
                            cv2.circle(image, (int(leye[0]), int(leye[1])), 15, eyesColor, thickness=2)
                            center = ((reye[0]+leye[0])/2, (reye[1]+leye[1])/2)
                            gazeTop = (center[0] + gazeLen * math.sin(math.radians(gaze[0])), center[1] + gazeLen * math.sin(math.radians(gaze[1])))
                            cv2.arrowedLine(image, (int(center[0]), int(center[1])), (int(gazeTop[0]), int(gazeTop[1])), gazeColor, thickness=2)

                        # Show the video
                        if displayFlag:
                            cv2.imshow('video', image)
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                video.release()
                                cv2.destroyAllWindows()
                                return
                        else:
                            if len(results) > 0:
                                print('    ', gaze)

                        writer.write(image)

                ### Main ######################################################################
                file = request.files['file']
                videoSource = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
                file.save(videoSource)
                print("videonSouse", videoSource)
                print("app",app.config['UPLOAD_FOLDER'])
                videoReader(videoSource)


            except:
                return render_template('index.html',massege = "解析出来ませんでした",color = "red")

            buf = io.BytesIO()
            image = Image.open(img)
            image.save(buf, 'png')
            qr_b64str = base64.b64encode(buf.getvalue()).decode("utf-8")
            qr_b64data = "data:image/png;base64,{}".format(qr_b64str)

            return render_template('index.html', img=qr_b64data, pre1_img_url=pre1_img_url, pre1_detail=pre1_detail, pre1_pro=pre1_pro, pre2_img_url=pre2_img_url, pre2_detail=pre2_detail, pre2_pro=pre2_pro, pre3_img_url=pre3_img_url, pre3_detail=pre3_detail, pre3_pro=pre3_pro)
    else:
        print("get request")

    return render_template('index.html')




@app.route('/uploads/<filename>')
# ファイルを表示する
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run()
