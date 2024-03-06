#!/bin/bash
[[ -z $1 ]] && echo "needs \$1 as WAV file to cut" && exit
[[ -z $2 ]] && echo "needs \$2 as App name (directory in source_out)" && exit

SRC="$1"
DST="/tmp/source_out/$2"
[[ ! -d "$DST" ]] && mkdir -p "$DST" && echo -e "\033[33m mkdir $DST\033[0m"

echo -e "\033[33mSRC: $SRC\033[0m"
echo -e "\033[33mDST: $DST\033[0m"
echo "enter to continue"
echo
read

ffmpeg -y -i "$SRC" -af atempo=4.0000,atempo=1.0000,asetrate=44100*11000/44000 "$DST"/note_045_A2.wav
ffmpeg -y -i "$SRC" -af atempo=3.7755,atempo=1.0000,asetrate=44100*11600/44000 "$DST"/note_046_A#2.wav
ffmpeg -y -i "$SRC" -af atempo=3.5636,atempo=1.0000,asetrate=44100*12300/44000 "$DST"/note_047_B2.wav
ffmpeg -y -i "$SRC" -af atempo=3.3637,atempo=1.0000,asetrate=44100*13000/44000 "$DST"/note_048_C3.wav
ffmpeg -y -i "$SRC" -af atempo=3.1748,atempo=1.0000,asetrate=44100*13800/44000 "$DST"/note_049_C#3.wav
ffmpeg -y -i "$SRC" -af atempo=2.9967,atempo=1.0000,asetrate=44100*14600/44000 "$DST"/note_050_D3.wav
ffmpeg -y -i "$SRC" -af atempo=2.8285,atempo=1.0000,asetrate=44100*15500/44000 "$DST"/note_051_D#3.wav
ffmpeg -y -i "$SRC" -af atempo=2.6697,atempo=1.0000,asetrate=44100*16400/44000 "$DST"/note_052_E3.wav
ffmpeg -y -i "$SRC" -af atempo=2.5199,atempo=1.0000,asetrate=44100*17400/44000 "$DST"/note_053_F3.wav
ffmpeg -y -i "$SRC" -af atempo=2.3784,atempo=1.0000,asetrate=44100*18500/44000 "$DST"/note_054_F#3.wav
ffmpeg -y -i "$SRC" -af atempo=2.2449,atempo=1.0000,asetrate=44100*19600/44000 "$DST"/note_055_G3.wav
ffmpeg -y -i "$SRC" -af atempo=2.1190,atempo=1.0000,asetrate=44100*20700/44000 "$DST"/note_056_G#3.wav
ffmpeg -y -i "$SRC" -af atempo=2.0000,atempo=1.0000,asetrate=44100*22000/44000 "$DST"/note_057_A3.wav
ffmpeg -y -i "$SRC" -af atempo=1.8878,atempo=1.0000,asetrate=44100*23300/44000 "$DST"/note_058_A#3.wav
ffmpeg -y -i "$SRC" -af atempo=1.7818,atempo=1.0000,asetrate=44100*24600/44000 "$DST"/note_059_B3.wav
ffmpeg -y -i "$SRC" -af atempo=1.6818,atempo=1.0000,asetrate=44100*26100/44000 "$DST"/note_060_C4.wav
ffmpeg -y -i "$SRC" -af atempo=1.5874,atempo=1.0000,asetrate=44100*27700/44000 "$DST"/note_061_C#4.wav
ffmpeg -y -i "$SRC" -af atempo=1.4983,atempo=1.0000,asetrate=44100*29300/44000 "$DST"/note_062_D4.wav
ffmpeg -y -i "$SRC" -af atempo=1.4142,atempo=1.0000,asetrate=44100*31100/44000 "$DST"/note_063_D#4.wav
ffmpeg -y -i "$SRC" -af atempo=1.3348,atempo=1.0000,asetrate=44100*32900/44000 "$DST"/note_064_E4.wav
ffmpeg -y -i "$SRC" -af atempo=1.2599,atempo=1.0000,asetrate=44100*34900/44000 "$DST"/note_065_F4.wav
ffmpeg -y -i "$SRC" -af atempo=1.1892,atempo=1.0000,asetrate=44100*36900/44000 "$DST"/note_066_F#4.wav
ffmpeg -y -i "$SRC" -af atempo=1.1224,atempo=1.0000,asetrate=44100*39200/44000 "$DST"/note_067_G4.wav
ffmpeg -y -i "$SRC" -af atempo=1.0595,atempo=1.0000,asetrate=44100*41500/44000 "$DST"/note_068_G#4.wav
ffmpeg -y -i "$SRC" -af atempo=1.0000,atempo=1.0000,asetrate=44100*44000/44000 "$DST"/note_069_A4.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*46600/44000,atempo=1.0000,atempo=0.9439 "$DST"/note_070_A#4.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*49300/44000,atempo=1.0000,atempo=0.8909 "$DST"/note_071_B4.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*52300/44000,atempo=1.0000,atempo=0.8409 "$DST"/note_072_C5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*55400/44000,atempo=1.0000,atempo=0.7937 "$DST"/note_073_C#5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*58700/44000,atempo=1.0000,atempo=0.7492 "$DST"/note_074_D5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*62200/44000,atempo=1.0000,atempo=0.7071 "$DST"/note_075_D#5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*65900/44000,atempo=1.0000,atempo=0.6674 "$DST"/note_076_E5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*69800/44000,atempo=1.0000,atempo=0.6300 "$DST"/note_077_F5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*73900/44000,atempo=1.0000,atempo=0.5946 "$DST"/note_078_F#5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*78300/44000,atempo=1.0000,atempo=0.5612 "$DST"/note_079_G5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*83000/44000,atempo=1.0000,atempo=0.5297 "$DST"/note_080_G#5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*88000/44000,atempo=1.0000,atempo=0.5000 "$DST"/note_081_A5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*93200/44000,atempo=1.0000,atempo=0.94387181,atempo=1/2 "$DST"/note_082_A#5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*98700/44000,atempo=1.0000,atempo=0.89089565,atempo=1/2 "$DST"/note_083_B5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*104600/44000,atempo=1.0000,atempo=0.84089823,atempo=1/2 "$DST"/note_084_C6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*110800/44000,atempo=1.0000,atempo=0.79370090,atempo=1/2 "$DST"/note_085_C#6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*117400/44000,atempo=1.0000,atempo=0.74915295,atempo=1/2 "$DST"/note_086_D6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*124400/44000,atempo=1.0000,atempo=0.70710561,atempo=1/2 "$DST"/note_087_D#6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*131800/44000,atempo=1.0000,atempo=0.66742004,atempo=1/2 "$DST"/note_088_E6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*139600/44000,atempo=1.0000,atempo=0.62996184,atempo=1/2 "$DST"/note_089_F6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*147900/44000,atempo=1.0000,atempo=0.59460263,atempo=1/2 "$DST"/note_090_F#6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*156700/44000,atempo=1.0000,atempo=0.56123165,atempo=1/2 "$DST"/note_091_G6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*166100/44000,atempo=1.0000,atempo=0.52973116,atempo=1/2 "$DST"/note_092_G#6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*176000/44000,atempo=1.0000,atempo=0.50000000,atempo=1/2 "$DST"/note_093_A6.wav
ffmpeg -y -i "$SRC" -af atempo=4.0000,atempo=1.0000,asetrate=44100*11000/44000 "$DST"/note_045_A2.wav
ffmpeg -y -i "$SRC" -af atempo=3.7755,atempo=1.0000,asetrate=44100*11600/44000 "$DST"/note_046_A#2.wav
ffmpeg -y -i "$SRC" -af atempo=3.5636,atempo=1.0000,asetrate=44100*12300/44000 "$DST"/note_047_B2.wav
ffmpeg -y -i "$SRC" -af atempo=3.3637,atempo=1.0000,asetrate=44100*13000/44000 "$DST"/note_048_C3.wav
ffmpeg -y -i "$SRC" -af atempo=3.1748,atempo=1.0000,asetrate=44100*13800/44000 "$DST"/note_049_C#3.wav
ffmpeg -y -i "$SRC" -af atempo=2.9967,atempo=1.0000,asetrate=44100*14600/44000 "$DST"/note_050_D3.wav
ffmpeg -y -i "$SRC" -af atempo=2.8285,atempo=1.0000,asetrate=44100*15500/44000 "$DST"/note_051_D#3.wav
ffmpeg -y -i "$SRC" -af atempo=2.6697,atempo=1.0000,asetrate=44100*16400/44000 "$DST"/note_052_E3.wav
ffmpeg -y -i "$SRC" -af atempo=2.5199,atempo=1.0000,asetrate=44100*17400/44000 "$DST"/note_053_F3.wav
ffmpeg -y -i "$SRC" -af atempo=2.3784,atempo=1.0000,asetrate=44100*18500/44000 "$DST"/note_054_F#3.wav
ffmpeg -y -i "$SRC" -af atempo=2.2449,atempo=1.0000,asetrate=44100*19600/44000 "$DST"/note_055_G3.wav
ffmpeg -y -i "$SRC" -af atempo=2.1190,atempo=1.0000,asetrate=44100*20700/44000 "$DST"/note_056_G#3.wav
ffmpeg -y -i "$SRC" -af atempo=2.0000,atempo=1.0000,asetrate=44100*22000/44000 "$DST"/note_057_A3.wav
ffmpeg -y -i "$SRC" -af atempo=1.8878,atempo=1.0000,asetrate=44100*23300/44000 "$DST"/note_058_A#3.wav
ffmpeg -y -i "$SRC" -af atempo=1.7818,atempo=1.0000,asetrate=44100*24600/44000 "$DST"/note_059_B3.wav
ffmpeg -y -i "$SRC" -af atempo=1.6818,atempo=1.0000,asetrate=44100*26100/44000 "$DST"/note_060_C4.wav
ffmpeg -y -i "$SRC" -af atempo=1.5874,atempo=1.0000,asetrate=44100*27700/44000 "$DST"/note_061_C#4.wav
ffmpeg -y -i "$SRC" -af atempo=1.4983,atempo=1.0000,asetrate=44100*29300/44000 "$DST"/note_062_D4.wav
ffmpeg -y -i "$SRC" -af atempo=1.4142,atempo=1.0000,asetrate=44100*31100/44000 "$DST"/note_063_D#4.wav
ffmpeg -y -i "$SRC" -af atempo=1.3348,atempo=1.0000,asetrate=44100*32900/44000 "$DST"/note_064_E4.wav
ffmpeg -y -i "$SRC" -af atempo=1.2599,atempo=1.0000,asetrate=44100*34900/44000 "$DST"/note_065_F4.wav
ffmpeg -y -i "$SRC" -af atempo=1.1892,atempo=1.0000,asetrate=44100*36900/44000 "$DST"/note_066_F#4.wav
ffmpeg -y -i "$SRC" -af atempo=1.1224,atempo=1.0000,asetrate=44100*39200/44000 "$DST"/note_067_G4.wav
ffmpeg -y -i "$SRC" -af atempo=1.0595,atempo=1.0000,asetrate=44100*41500/44000 "$DST"/note_068_G#4.wav
ffmpeg -y -i "$SRC" -af atempo=1.0000,atempo=1.0000,asetrate=44100*44000/44000 "$DST"/note_069_A4.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*46600/44000,atempo=1.0000,atempo=0.9439 "$DST"/note_070_A#4.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*49300/44000,atempo=1.0000,atempo=0.8909 "$DST"/note_071_B4.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*52300/44000,atempo=1.0000,atempo=0.8409 "$DST"/note_072_C5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*55400/44000,atempo=1.0000,atempo=0.7937 "$DST"/note_073_C#5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*58700/44000,atempo=1.0000,atempo=0.7492 "$DST"/note_074_D5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*62200/44000,atempo=1.0000,atempo=0.7071 "$DST"/note_075_D#5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*65900/44000,atempo=1.0000,atempo=0.6674 "$DST"/note_076_E5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*69800/44000,atempo=1.0000,atempo=0.6300 "$DST"/note_077_F5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*73900/44000,atempo=1.0000,atempo=0.5946 "$DST"/note_078_F#5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*78300/44000,atempo=1.0000,atempo=0.5612 "$DST"/note_079_G5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*83000/44000,atempo=1.0000,atempo=0.5297 "$DST"/note_080_G#5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*88000/44000,atempo=1.0000,atempo=0.5000 "$DST"/note_081_A5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*93200/44000,atempo=1.0000,atempo=0.94387181,atempo=1/2 "$DST"/note_082_A#5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*98700/44000,atempo=1.0000,atempo=0.89089565,atempo=1/2 "$DST"/note_083_B5.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*104600/44000,atempo=1.0000,atempo=0.84089823,atempo=1/2 "$DST"/note_084_C6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*110800/44000,atempo=1.0000,atempo=0.79370090,atempo=1/2 "$DST"/note_085_C#6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*117400/44000,atempo=1.0000,atempo=0.74915295,atempo=1/2 "$DST"/note_086_D6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*124400/44000,atempo=1.0000,atempo=0.70710561,atempo=1/2 "$DST"/note_087_D#6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*131800/44000,atempo=1.0000,atempo=0.66742004,atempo=1/2 "$DST"/note_088_E6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*139600/44000,atempo=1.0000,atempo=0.62996184,atempo=1/2 "$DST"/note_089_F6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*147900/44000,atempo=1.0000,atempo=0.59460263,atempo=1/2 "$DST"/note_090_F#6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*156700/44000,atempo=1.0000,atempo=0.56123165,atempo=1/2 "$DST"/note_091_G6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*166100/44000,atempo=1.0000,atempo=0.52973116,atempo=1/2 "$DST"/note_092_G#6.wav
ffmpeg -y -i "$SRC" -af asetrate=44100*176000/44000,atempo=1.0000,atempo=0.50000000,atempo=1/2 "$DST"/note_093_A6.wav









