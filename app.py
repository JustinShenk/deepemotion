import base64
import glob
import logging
import sys
import uuid

__version__ = '0.0.1'

try:
    import cv2
except:
    sys.path.append('/usr/lib/python3/dist-packages')
    import cv2
import matplotlib
matplotlib.use('Agg')

import json
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

pd.set_option('display.width', 1000)
pd.set_option('colheader_justify', 'center')

app = Flask(__name__)
app.config.from_pyfile('config.cfg')

os.environ['EMOTION_API_URL'] = app.config.get('EMOTION_API_URL', '')
os.environ['EMOTION_API_TOKEN'] = app.config.get('EMOTION_API_TOKEN', '')
os.environ['FLASK_INSTANCE_PATH'] = app.instance_path

UPLOAD_FOLDER = os.path.join(app.instance_path, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024  # 30 MB limit
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
current_df = pd.DataFrame()
SAMPLE_FILE = os.path.join(app.static_folder, "sample.mp4")
ret, _ = cv2.VideoCapture(SAMPLE_FILE).read()
assert ret, "OpenCV installed at {} does not support video".format(
    cv2.__file__)

global detector, graph
sns.set()

detector = FER(emotion_model=os.environ.get('EMOTION_API_URL', None))

current_video = None


def read_csv(file):
    position_df = pd.read_csv(file, index_col='time_stamps_vec')[['x', 'y']]
    position_df *= 100
    return position_df


def calc_distance(position_df):
    position_df['distance'] = np.sqrt(
        np.power(position_df['x'].shift() - position_df['x'], 2) +
        np.power(position_df['y'].shift() - position_df['y'], 2))
    return position_df


def allowed_file(filename):
    allowed = '.' in filename and \
           filename.rsplit('.', 1)[-1].lower() in ['mp4','avi','mov','mpg','mkv','webm']
    if not allowed:
        app.logger.error(filename + " not allowed")
    return allowed


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
    current_video = Video(
        filename, outdir='/tmp', tempfile=to_uploads('temp_outfile.mp4'))
    return current_video


def get_frame(video_obj, frame_nr=0, encoding='base64'):
    try:
        for i in range(frame_nr + 1):
            ret, frame = video_obj.cap.read()
    except:
        app.logger.error("Less than {} frames in video".format(frame_nr))
    video_obj.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    h, w = frame.shape[:2]
    # TODO: resize based on image size
    frame = cv2.resize(
        frame, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_CUBIC)
    if encoding is 'opencv':
        return frame
    elif encoding is 'base64':
        _, buffer = cv2.imencode('.jpg', frame)
        b64image = base64.b64encode(buffer)
        data_url = b'data:image/jpeg;base64,' + b64image
        return data_url.decode('utf8')


def get_output_images(video_id, outdir, nr=3):
    files = glob.glob(os.path.join(outdir, f'{video_id}*.jpg'))
    # TODO Implement buckets for storage
    # Move to static directory for serving
    target_dir = app.static_folder
    local_files = []
    for file in files:
        target = to_uploads(os.path.basename(file))
        os.rename(file, target)
        local_files.append(''.join(target.split('/instance/')[-1]))
    # Get relative path
    total_files = len(local_files)
    if total_files <= nr:
        return files
    output_images = []
    for idx, interval_idx in enumerate(
            range(0, total_files, total_files // nr)):
        output_images.append(local_files[idx])
        if idx + 1 == nr:
            break
    return output_images


@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    global current_df, current_video, graph
    app.logger.info("/upload accessed")
    if request.method == 'POST':
        preview = False
        # check if the post request has the file part
        file = request.files.get('files[]')
        app.logger.info("{} - File received".format(file.filename))
        if not file:
            # flash('No file part', category="Error")
            app.logger.error('No file part')
            return redirect(request.url)
        # if user does not select file, browser also
        # submits an empty part without filename
        if file.filename == '':
            # flash('No selected file', category="Error")
            return redirect(request.url)
        elif file and not allowed_file(file.filename):
            flash('Filename {} not allowed. Try with mp4 files'.format(
                file.filename))
        elif file and allowed_file(file.filename):
            session.clear()
            # Save video
            filename = secure_filename(file.filename)
            session['complete_video'] = request.files.get(
                'completeVideo', False)
            mp4path = to_uploads(filename)
            file.save(mp4path)
            app.logger.info("Saved to {}".format(mp4path))
            current_video = load_video(mp4path)
            # Save screenshots with emotion labels
            screenshot = get_frame(current_video, encoding='opencv')
            cv2.imwrite(to_uploads('screenshot.png'), screenshot)
            session['screenshot'] = 'screenshot.png'
            session['filename'] = filename
            session['loaded'] = True
            results = analyze()
            os.remove(mp4path)
            return results
        app.logger.error("Error with analysis")
        return False
    # return redirect(url_for('analyze'))


def remove_frames(folder):
    files = glob.glob(os.path.join(folder, 'frame*.jpg'))
    for file in files:
        os.remove(file)


@app.route('/analyze', methods=['GET'])
def analyze():
    """Process analyze request."""
    global current_df, current_video, graph
    results = []
    output = {}
    # Remove previous frames
    remove_frames(app.config['UPLOAD_FOLDER'])

    # Analyze video and save every nth frame
    try:
        assert current_video.cap.get(
            cv2.CAP_PROP_FRAME_HEIGHT) > 0, 'Video not loaded correctly'
        frequency = 1 if session['complete_video'] else 20
        app.logger.info("Analyzing every {} frame".format(frequency))
        # Analyze video and get dataframe with emotions
        video_id = str(uuid.uuid4())[:9]
        df = current_video.analyze(
            detector,
            display=False,
            frequency=frequency,
            video_id=video_id,
            max_results=None if app.debug else 10,
            output='pandas')
        if df.dropna().empty:
            # flash('No faces detected in sampled frames of {}'.format(current_video.filename()),'error')
            app.logger.error(
                'No faces detected in sampled frames of {}'.format(
                    current_video.filename()))
            return Response('Upload failed', status=300)
        elif len(df.dropna()) == 1:
            # flash('Only one of sample frames found with face - try another video.','error')
            app.logger.error(
                "Only one sample frame found with face - try another video")
    except AttributeError:
        app.logger.error('current_video is NoneType')
        return Response('Upload failed', status=500)
    root, ext = os.path.splitext(session.get('filename'))
    video_outfile = root + '_output' + ext

    if not os.path.isfile(to_uploads(video_outfile)):
        # flash('Video output.mp4 not found on server','error')
        app.logger.error("Video {} not found on server".format(
            to_uploads(video_outfile)))
    session['video_filename'] = video_outfile
    current_df = current_video.get_first_face(df).dropna()
    csvpath = ''.join(session['filename'].split('.')[:-1]) + '.csv'
    csvpath = to_uploads(csvpath)
    current_df.to_csv(csvpath)
    session['csv_filename'] = os.path.split(csvpath)[1]
    session['dataframe'] = current_df.head(5).to_html(
        float_format=lambda x: '%.2f' % x, classes='mystyle')

    # session['dataframe'] = current_df.head(10).style.format('%.2f').render()
    session['output_images'] = get_output_images(video_id,
                                                 current_video.outdir)
    emotions = current_video.get_emotions(current_df)
    try:
        emotions.plot()
    except TypeError:
        # flash('Empty DataFrame', 'error')
        app.logger.error("Empty dataframe")
        return False
    plot_filename = f"{session.get('filename')}-emotions-chart.png"
    emotions_chart_path = to_uploads(plot_filename)
    plt.savefig(emotions_chart_path)
    session['emotions_chart'] = f'uploads/{plot_filename}'
    session['explore'] = True
    result = jsonify({
        'files': [{
            'url': (f'uploads/{video_outfile}'),
            'name': session['filename'],
            'screenshots': session.get('output_images'),
            'plot_url': session['emotions_chart'],
            'dataframe': session.get('dataframe')
        }]
    })
    return result


@app.route('/', methods=['GET', 'POST'])
def index():
    global current_df, current_video, graph
    return render_template('index.html', **session)


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
    app.run(host='0.0.0.0', port=5000)
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
