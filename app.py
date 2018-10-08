import base64
import glob
import time
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
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, \
    make_response, jsonify, Response
import keras.backend as K
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = b'secret_key'
UPLOAD_FOLDER = os.path.join(app.instance_path, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024 # 30 MB limit
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
current_df = pd.DataFrame()
SAMPLE_FILE = os.path.join(app.static_folder, "test.mp4")

global detector, graph
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
           filename.rsplit('.', 1)[-1].lower() in ['mp4','avi','mov','mpg']
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

def to_uploads(filename):
    return os.path.join(app.config['UPLOAD_FOLDER'], filename)

def load_video(filename):
    global current_video
    current_video = Video(filename,
                          outdir=app.config['UPLOAD_FOLDER'],
                          tempfile=to_uploads('temp_outfile.mp4'))
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
    if encoding is 'opencv':
        return frame
    elif encoding is 'base64':
        retval, buffer = cv2.imencode('.jpg', frame)
        b64image = base64.b64encode(buffer)
        data_url = b'data:image/jpeg;base64,' + b64image
        return data_url.decode('utf8')

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

@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/upload', methods=['GET','POST'])
def upload():
    global current_df, current_video, graph
    app.logger.info("/upload accessed")
    if request.method == 'POST':
        preview = False
        # check if the post request has the file part
        file = request.files.get('file')
        app.logger.info("{} - File received".format(file.filename))
        if not file:
            flash('No file part', category="Error")
            app.logger.error('No file part')
            return redirect(request.url)
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', category="Error")
            return redirect(request.url)
        elif file and not allowed_file(file.filename):
            flash('Filename {} not allowed. Try with mp4 files'.format(file.filename))
        elif file and allowed_file(file.filename):
            session.clear()
            filename = secure_filename(file.filename)
            session['complete_video'] = request.files.get('completeVideo',False)
            mp4path = to_uploads(filename)
            file.save(mp4path)
            app.logger.info("Saved to {}".format(mp4path))
            current_video = load_video(mp4path)
            screenshot = get_frame(current_video, encoding='opencv')
            cv2.imwrite(to_uploads('screenshot.png'), screenshot)
            session['screenshot'] = 'screenshot.png'
            session['filename'] = filename
            session['loaded'] = True
    return redirect(url_for('analyze'))

@app.route('/analyze', methods=['GET'])
def analyze():
    """Process analyze request."""
    global current_df, current_video, graph
    output = {}
    # Remove previous frames
    [os.remove(f) for f in glob.glob(to_uploads('frame*.jpg'))]
    # Analyze video and save every 50th frame
    try:
        assert current_video.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) > 0, 'Video not loaded correctly'
        frequency = 1 if session['complete_video'] else 20
        app.logger.info("Analyzing every {} frame".format(frequency))
        df = current_video.analyze(detector, display=False, frequency=frequency, output='pandas')
        if df.dropna().empty:
            flash('No faces detected in sampled frames of {}'.format(current_video.filename()),'error')
            return Response('Upload failed', status=300)
        elif len(df.dropna()) == 1:
            flash('Only one of sample frames found with face - try another video.','error')
    except AttributeError:
        flash('current_video is NoneType', 'error')
        return Response('Upload failed', status=500)
    video_outfile = 'output.mp4'
    if not os.path.isfile(to_uploads(video_outfile)):
        flash('Video output.mp4 not found on server','error')
    session['video_filename'] = video_outfile
    current_df = current_video.get_first_face(df).dropna()
    csvpath = ''.join(session['filename'].split('.')[:-1]) + '.csv'
    csvpath = to_uploads(csvpath)
    current_df.to_csv(csvpath)
    session['csv_filename'] = os.path.split(csvpath)[1]
    session['dataframe'] = current_df.head(10).to_html(float_format=lambda x: '%.2f' % x)
    session['output_images'] = get_output_images(current_video.outdir)
    emotions = current_video.get_emotions(current_df)
    try:
        emotions.plot()
    except TypeError:
        flash('Empty DataFrame', 'error')
        return Response('Upload error', status=500)
    emotions_chart = to_uploads('emotions_chart.png')
    plt.savefig(emotions_chart)
    session['emotions_chart'] = 'emotions_chart.png'
    session['explore'] = True
    return Response('Uploaded successfully', status=200)

@app.route('/', methods=['GET', 'POST'])
def index():
    global current_df, current_video, graph
    output = {}
    # Load and display sample file
    if request.args.get('action') == 'load_sample':
        session.pop('explore', None)
        filename = SAMPLE_FILE.split('/')[-1]
        current_video = load_video(SAMPLE_FILE)
        screenshot = get_frame(current_video, encoding='opencv')
        cv2.imwrite(to_uploads('screenshot.png'), screenshot)
        session['screenshot'] = 'screenshot.png'
        session['filename'] = filename
        session['loaded'] = True

    if request.args.get('action') == 'analyze':
        response = analyze()
        return redirect('/')
    #     session['explore'] = True
    #     # Remove previous frames
    #     [os.remove(f) for f in glob.glob(to_uploads('frame*.jpg'))]
    #     # Analyze video and save every 50th frame
    #     with graph.as_default():
    #         raw_data = current_video.analyze(detector, display=False, frequency=30)
    #     video_outfile = 'output.mp4'
    #     assert os.path.isfile(to_uploads(video_outfile)), app.logger.error("no output.mp4")
    #     session['video_filename'] = 'output.mp4'
    #     df = current_video.to_pandas(raw_data)
    #     current_df = current_video.get_first_face(df).dropna()
    #     csvpath = ''.join(session['filename'].split('.')[:-1]) + '.csv'
    #     csvpath = to_uploads(csvpath)
    #     current_df.to_csv(csvpath)
    #     output['csv_filename'] = os.path.split(csvpath)[1]
    #     output['dataframe'] = current_df.head(10).to_html(float_format=lambda x: '%.2f' % x)
    #     output['output_images'] = get_output_images(current_video.outdir)
    #     emotions = current_video.get_emotions(current_df)
    #     emotions.plot()
    #     emotions_chart = to_uploads('emotions_chart.png')
    #     plt.savefig(emotions_chart)
    #     output['emotions_chart'] = 'emotions_chart.png'
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
