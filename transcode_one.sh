#!/bin/sh

# 1) определяем формат: mp4 или flv
# 2) если mp4, то ремуксуем в flv
# 3) на flv напускаем yamdi
# 4) делаем из flv скриншот
# 5) помещаем в облако
# 6) создаём файл-задание
# см. README 

PYTHON=python

prepare(){
    echo $1
    echo $2

    FNAME=$1
    THUMB=$2
    ACCOUNT_ID=$3
    VIDEO_ID=$4
    NEED_HLS=$5

    ROOT_PATH=$(cd $(dirname $0) && pwd);

    # определяем формат
    if ffmpeg -i $FNAME 2>&1|grep "Input #0, flv"
      then 
	echo "FLV"
      else 
	echo "MP4"
	remux $FNAME
    fi

    # напускаем yamdi и результатом заменяем исходный файл,  делаем скриншот
    # TODO: копируем в облако + делаем файл-задание
    yamdi -i $FNAME -o $FNAME.nm \
	   && mv -f $FNAME.nm $FNAME \
           && ffmpeg  -y -itsoffset -4  -i $FNAME -vcodec mjpeg -vframes 1 -an -f rawvideo -s 640x480 $THUMB 2>/dev/null \
	   && $PYTHON $ROOT_PATH/move_to_s3.py $FNAME $ACCOUNT_ID $VIDEO_ID $NEED_HLS
    
	   #&& $ROOT_PATH/make_frag.sh $FNAME $FRAG_PATH \
	   #&& $ROOT_PATH/make_hls.sh $FNAME $HLS_PATH \
	   #&& touch $FNAME"_READY"
}

remux() {
  # делаем ремукс в tmp-файл а затем замещаем им прежний 
  FNAME=$1  
  TMP="$1_tmp"
  echo "REMUX $FNAME"
  ffmpeg -y -i $FNAME -vcodec copy -acodec copy -f flv $TMP  2>/dev/null &&  mv -f $TMP $FNAME
}

prepare $1 $2 $3 $4 $5