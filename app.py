import base64
import glob
import urllib

import cv2
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import seaborn as sns

from fer.fer import FER
from fer.classes import Video
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
import keras.backend as K
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = b'secret_key'
UPLOAD_FOLDER = os.path.join(app.instance_path, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024 # 30 MB limit for 1 day
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
current_df = pd.DataFrame()
SAMPLE_FILE = os.path.join(app.config['UPLOAD_FOLDER'], "test.mp4")
try:
    os.rename('test.mp4', SAMPLE_FILE)
except:
    pass

global detector, graph
graph = K.get_session().graph
sns.set()

detector = FER()
current_video = None

def read_csv(file):
    position_df = pd.read_csv(file, index_col='time_stamps_vec')[['x', 'y']]
    position_df *= 100
    return position_df

def calc_distance(position_df):
    position_df['distance'] = np.sqrt(np.power(position_df['x'].shift() - position_df['x'], 2) +
                                   np.power(position_df['y'].shift() - position_df['y'], 2))
    return position_df

def allowed_file(filename):
    allowed = '.' in filename and \
           filename.rsplit('.', 1)[-1].lower() in ['mp4']
    if not allowed:
        app.logger.error(filename + " not allowed")
    return allowed


def analyze_df(position_df):
    global current_df
    try:
        position_df = calc_distance(position_df)
        current_df = position_df
    except Exception as e:
        app.logger.error(e)
    return position_df


def display_file(csvpath):
    position_df = read_csv(csvpath)
    return position_df

def format_plot(column, columns=None, overlay=False):
    plt.ylabel("Frequency")
    plt.xlabel("cm")
    plt.legend()


def get_plots(columns, overlay=False):
    plots = {}
    for column in columns:
        if overlay:
            plt.hist(current_df[column], label=column)
            format_plot(column, columns, overlay)
            basename = ''.join(session.get('filename').split('.csv')[0])
            plot_filename = "{}_{}.png".format(basename, ','.join(columns))
            plot_url = os.path.join(app.config['UPLOAD_FOLDER'], plot_filename)
            if column is columns[-1]:
                if os.path.isfile(plot_url):
                    os.remove(plot_url)
                plt.savefig(plot_url)
                plots[','.join(columns)] = plot_filename
        else:
            plt.clf()
            plt.subplots()
            plt.hist(current_df[column], label=column)
            format_plot(column)
            basename = ''.join(session.get('filename').split('.csv')[0])
            plot_filename = "{}_{}.png".format(basename, column)
            plot_url = os.path.join(app.config['UPLOAD_FOLDER'], plot_filename)
            app.logger.info(plot_filename, plot_url)
            if os.path.isfile(plot_url):
                os.remove(plot_url)
            plt.savefig(plot_url)
            plots[column] = plot_filename
    app.logger.info(plots)
    return plots


def load_video(filename):
    global current_video
    current_video = Video(filename,
                          outdir=app.config['UPLOAD_FOLDER'],
                          tempfile=os.path.join(app.config['UPLOAD_FOLDER'],'temp_outfile.mp4'))
    return current_video

def get_frame(video_obj, frame_nr=0, encoding = 'base64'):
    try:
        for i in range(frame_nr+1):
            ret, frame = video_obj.cap.read()
    except:
        app.logger.error("Less than {} frames in video".format(frame_nr))
    video_obj.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    h, w = frame.shape[:2]
    frame = cv2.resize(frame, (0,0), fx=0.5, fy=0.5, interpolation=cv2.INTER_CUBIC)
    if encoding is 'base64':
        retval, buffer = cv2.imencode('.jpg', frame)
        b64image = base64.b64encode(buffer)
        data_url = b'data:image/jpeg;base64,' + b64image
        return data_url.decode('utf8')
    return frame

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/upload', methods=['GET','POST'])
def upload():
    global current_df, current_video, graph
    output = {}
    app.logger.info("/upload accessed")
    if request.method == 'POST':
        # check if the post request has the file part
        file = request.files.get('file')
        app.logger.info("{} - File received".format(file.filename))
        if not file:
            flash('No file part', category="Error")
            app.logger.info('No file part')
            return redirect(request.url)
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', category="Error")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            mp4path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(mp4path)
            app.logger.info("Saved to {}".format(mp4path))
            current_video = load_video(mp4path)
            screenshot = get_frame(current_video, encoding = 'base64')
            output['screenshot'] = screenshot
            # current_df = display_file(mp4path)
            output['dataframe'] = current_df.head(1).to_html(float_format=lambda x: '%.2f' % x)
            session['filename'] = filename
            session['loaded'] = True
    return render_template('index.html', **output, **session)


def get_output_images(outdir, nr=3):
    files = glob.glob(os.path.join(outdir,'frame*.jpg'))
    # Get relative path
    files = [''.join(file.split('/instance/')[-1]) for file in files]
    total_files = len(files)
    if total_files <= nr:
        return files
    output_images = []
    for idx, interval_idx in enumerate(range(0, len(files), total_files//nr)):
        output_images.append(files[idx])
        if idx+1 == nr:
            break
    return output_images


@app.route('/', methods=['GET', 'POST'])
def index():
    global current_df, current_video, graph
    output = {}
    if request.args.get('action') == 'reset':
        session.clear()
        return redirect(url_for('index'))
    # Load and display sample file
    if request.args.get('action') == 'load_sample':
        app.logger.info("loading sample")
        filename = SAMPLE_FILE.split('/')[-1]
        current_video = load_video(SAMPLE_FILE)
        screenshot = get_frame(current_video, encoding = 'base64')
        output['screenshot'] = screenshot
        session['filename'] = filename
        session['loaded'] = True
        session.pop('explore', None)
    if request.args.get('action') == 'analyze':
        session['explore'] = True
        # Remove previous frames
        [os.remove(f) for f in glob.glob(os.path.join(app.config['UPLOAD_FOLDER'],'frame*.jpg'))]

        # Analyze video and save every 50th frame
        with graph.as_default():
            raw_data = current_video.analyze(detector, display=False, frequency=30)
        video_outfile = 'output.mp4'
        assert os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], video_outfile)), app.logger.error("no output.mp4")
        session['video_filename'] = 'output.mp4'
        df = current_video.to_pandas(raw_data)
        current_df = current_video.get_first_face(df).dropna()
        csvpath = ''.join(session['filename'].split('.')[:-1]) + '.csv'
        csvpath = os.path.join(app.config['UPLOAD_FOLDER'], csvpath)
        current_df.to_csv(csvpath)
        output['csv_filename'] = os.path.split(csvpath)[1]
        output['dataframe'] = current_df.head(10).to_html(float_format=lambda x: '%.2f' % x)
        output['output_images'] = get_output_images(current_video.outdir)
        emotions = current_video.get_emotions(current_df)
        emotions.plot()
        emotions_chart = os.path.join(app.config['UPLOAD_FOLDER'], 'emotions_chart.png')
        plt.savefig(emotions_chart)
        output['emotions_chart'] = 'emotions_chart.png'
    # if request.args.get('hist_plot'):
    #     overlay = request.args.get('overlayCheck')
    #     columns = request.args.getlist('hist_plot')
    #     app.logger.info(columns)
    #     session['analysis'] = 'hist_plot'
    #     output['plots'] = get_plots(columns, overlay)
    return render_template('index.html', **output, **session)

@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

if __name__ == '__main__':
    app.run()
