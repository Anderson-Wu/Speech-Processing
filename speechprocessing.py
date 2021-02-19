import librosa
import matplotlib.pyplot as plt
import librosa.display
import numpy as np
import math
from scipy.ndimage import gaussian_filter

wave,freq = librosa.load('voice.wav',sr=None)
frameSize = math.ceil(freq*0.032)
plt.figure(figsize=(20, 4))
librosa.display.waveplot(wave, sr=freq)
plt.xlabel('Time(S)')
plt.ylabel('Amplitude')
plt.title('1-Waveform')
plt.show()


def energy(wave,frameSize):
    total_len = len(wave)
    frameBlock = frameSize;
    frameNum = math.ceil(total_len/frameBlock)
    energy = np.zeros(frameNum)
    for i in range(frameNum):
        current = wave[np.arange(i*frameBlock,min(i*frameBlock+frameSize,total_len))]
        sum = 0
        for j in range((len(current)-1)):
            sum += current[j]*current[j]
        energy[i] = sum
    return energy


energy = energy(wave,frameSize)
plt.figure(figsize=(20, 4))
time = np.arange(0,len(energy))*(len(wave)/len(energy)/freq)
plt.xlabel('Time(S)')
plt.ylabel('Volume')
plt.title('2-Energy contour')
plt.plot(time,energy)
plt.show()


def zero_crossing_rate(wave,frameSize):
    total_len = len(wave)
    frameBlock = frameSize;
    frameNum = math.ceil(total_len/frameBlock)
    zcr = np.zeros(frameNum)
    for i in range(frameNum):
        current = wave[np.arange(i*frameBlock,min(i*frameBlock+frameSize,total_len))]
        sum = 0
        for j in range((len(current)-1)):
            if(current[j]*current[j+1] <=0):
                sum += 1
        zcr[i] = sum
    return zcr

zcr = zero_crossing_rate(wave,frameSize)
plt.figure(figsize=(20, 4))
time = np.arange(0,len(energy))*(len(wave)/len(energy)/freq)
plt.xlabel('Time(S)')
plt.ylabel('Count')
plt.title('3-Zero crossing rate')
plt.plot(time,zcr)
plt.show()


def endpoint(energy,zcr):
    sum = 0
    energy_avg = 0
    for en in energy :
        sum = sum + en
    energy_avg = sum / len(energy)

    sum = 0
    ITL = (energy[0]+energy[1]+energy[2]+energy[3]+energy[4]) / 5
    ITU = energy_avg / 2
    ITL = (ITL + ITU) / 2

    IZCT = (zcr[0]+zcr[1]+zcr[2]+zcr[3]+zcr[4])/ 5

    fir = []
    sec = []
    thr = []

    flag = 0
    for i in range(len(energy)):
        if len(fir) == 0 and flag == 0 and energy[i] > ITU :
            fir.append(i)
            flag = 1
        elif flag == 0 and energy[i] > ITU and i - 21 > fir[len(fir) - 1]:
            fir.append(i)
            flag = 1
        elif flag == 0 and energy[i] > ITU and i - 21 <= fir[len(fir) - 1]:
            fir = fir[:len(fir) - 1]
            flag = 1

        if flag == 1 and energy[i] <ITU :
            fir.append(i)
            flag = 0

    for j in range(len(fir)) :
        i = fir[j]
        if j % 2 == 1 :
            while i < len(energy) and energy[i] > ITL :
                i = i + 1
            sec.append(i)
        else :
            while i > 0 and energy[i] > ITL :
                i = i - 1
            sec.append(i)

    for j in range(len(sec)) :
        i = sec[j]
        if j % 2 == 1 :
            while i < len(zcr) and zcr[i] >= 3 * IZCT :
                i = i + 1
            thr.append(i)
        else :
            while i > 0 and zcr[i] >= 3 * IZCT :
                i = i - 1
            thr.append(i)

    return thr

endpoint = endpoint(energy,zcr)
plt.figure(figsize=(20, 4))
librosa.display.waveplot(wave,sr=freq)
plt.xlabel('Time(S)')
plt.ylabel('Amplitude')
plt.title('4-End point detection')
plt.axvline(x=endpoint[0]*frameSize/freq ,color='red')
plt.axvline(x=endpoint[-1]*frameSize/freq,color='red')
plt.show()



def pitch(wave,frameSize,energy):
    total_len = len(wave)
    frameBlock = frameSize;
    frameNum = math.ceil(total_len / frameBlock)
    pitch = np.zeros(frameNum)
    threshold= (energy[0]+energy[1]+energy[2]+energy[3]+energy[4]+energy[5]) / 6
    for i in range(frameNum):
        current = wave[np.arange(i*frameBlock,min(i*frameBlock+frameSize,total_len))]
        length = len(current)
        ac = np.zeros(length)

        for k in range(0,length-1):
            value = 0
            for n in range(k,length):
                value += current[n]*current[n-k]
            ac[k] = value

            ac = gaussian_filter(ac,5)

            peaks = []

            index = 1
            index_2 = 0
            while (index < (len(ac) - 1)):
                if ((ac[index - 1] < ac[index]) and (ac[index + 1] <= ac[index])):
                    if (ac[index + 1] == ac[index]):
                        index_2 = index + 1
                        while (index_2 < (len(ac)) and ac[index_2] == ac[index]):
                            index_2 = index_2 + 1
                        if (index_2 == len(ac)):
                            peaks.append(index)
                            break;
                        if (ac[index_2] < ac[index]):
                            peaks.append(index)
                            index = index_2
                    else:
                        peaks.append(index)
                        index = index + 1
                else:
                    index = index + 1

            if (len(peaks) < 2):
                pitch[i] = 0
            elif energy[i] < threshold:
                pitch[i] = 0
            else:
                y = np.argsort(ac)
                fir = -1
                while y[fir] not in peaks:
                    fir = fir - 1
                sec = fir - 1
                while y[sec] not in peaks:
                    sec = sec - 1

                f = freq / (abs(y[fir] - y[sec]))
                if (f >= 40 and f <= 1000):
                    pitch[i] = (f)
                else:
                    pitch[i] = 0
       
    final_pitch = np.zeros(frameNum)
    med = np.zeros(5)
    for a in range(len(pitch) - 4):
        med[0] = pitch[a]
        med[1] = pitch[a + 1]
        med[2] = pitch[a + 2]
        med[3] = pitch[a + 3]
        med[4] = pitch[a + 4]
        med.sort()
        final_pitch[a + 2] = med[2]
    final_pitch[0] = 0
    final_pitch[1] = 0
    final_pitch[-1] = 0
    final_pitch[-2] = 0

    plt.figure(figsize=(20, 4))
    time = np.arange(0,len(energy))*(len(wave)/len(energy)/freq)
    plt.xlabel('Time(S)')
    plt.ylabel('Pitch')
    plt.title('5-Pitch contour')
    plt.plot(time,final_pitch)
    plt.show()

pitch(wave,frameSize,energy)
