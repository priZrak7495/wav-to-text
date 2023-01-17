#!/usr/bin/python3
import json
import os
import subprocess
import wave
from datetime import timedelta
from vosk import Model, KaldiRecognizer, SetLogLevel
import srt
import pysubs2

path = './' #путь к скрипту
SetLogLevel(-1)

def recognize_wav(file_name):
    fn = os.path.basename(file_name).replace("_", " ").replace(".wav", "") + '\n'
    sample_rate = 16000
    #os.system('unlink ' + path + '/left.wav')
    #os.system('unlink ' + path + '/right.wav')

    wavefile = wave.open(file_name, 'r')
    channels = wavefile.getnchannels()
    text = ''

    if channels == 2:
        os.system(
            'ffmpeg -loglevel quiet -i "' + file_name + '" -map_channel 0.0.0 /opt/TBOT/left.wav -map_channel 0.0.1 /opt/TBOT/right.wav')
        left = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i',
                                 path + '/left.wav', '-ar', str(sample_rate), '-ac', '1', '-f', 's16le', '-'],
                                stdout=subprocess.PIPE)
        a = transcribe(left)
        right = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i',
                                  path + 'right.wav', '-ar', str(sample_rate), '-ac', '1', '-f', 's16le', '-'],
                                 stdout=subprocess.PIPE)
        b = transcribe(right)
        c = srt.compose(a + b)
        os.system('unlink ' + path + '/subtitles.srt')
        with open(path + "/subtitles.srt", "w") as fp:
            fp.write(c)
        subs = pysubs2.load(path + "/subtitles.srt")
        for line in subs:
            text += line.text + '\n'
    else:
        process = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i',
                                    file_name, '-ar', str(sample_rate), '-ac', '1', '-f', 's16le', '-'],
                                   stdout=subprocess.PIPE)
        a = transcribe(process)
        c = srt.compose(a)
        os.system('unlink ' + path + '/subtitles.srt')
        with open(path + "/subtitles.srt", "w") as fp:
            fp.write(c)
        subs = pysubs2.load(path + "/subtitles.srt")
        for line in subs:
            text += line.text + '\n'
    print('Результат:\n' + text)


def transcribe(process):
    sample_rate = 16000
    model = Model("/opt/vosk-model-ru") #путь к моделям
    rec = KaldiRecognizer(model, sample_rate)
    rec.SetWords(True)
    WORDS_PER_LINE = 126
    results = []
    subs = []
    while True:
        data = process.stdout.read(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            results.append(rec.Result())
    results.append(rec.FinalResult())

    for i, res in enumerate(results):
        jres = json.loads(res)
        if not 'result' in jres:
            continue
        words = jres['result']
        for j in range(0, len(words), WORDS_PER_LINE):
            line = words[j: j + WORDS_PER_LINE]
            s = srt.Subtitle(index=len(subs),
                             content=" ".join([l['word'] for l in line]),
                             start=timedelta(seconds=line[0]['start']),
                             end=timedelta(seconds=line[-1]['end']))
            subs.append(s)
    return subs


recognize_wav(path + '/voice.wav') #путь к аудиофайлу
