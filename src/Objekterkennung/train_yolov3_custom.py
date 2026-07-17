# YOLOv3-Training in Google Colaboratory.
# Dieses Skript wird zellenweise in einem Colab-Notebook ausgeführt;
# Zeilen mit "!" bzw. "%" sind Colab-Shell-Magics und keine Python-Syntax.

import glob
from typing import List

from google.colab import drive

DATASET_ARCHIVE: str = "/mydrive/custom_object_detection/Dataset.zip"
CUSTOM_OBJECTS: List[str] = ["Bio", "Schachtel", "Papier", "Dose"]

# 1 – Google Drive einbinden
drive.mount("/content/gdrive")
# !ln -s /content/gdrive/My\ Drive/ /mydrive
# !ls /mydrive

# 2 – Darknet klonen und mit GPU-/OpenCV-Unterstützung bauen
# !git clone https://github.com/AlexeyAB/darknet.git
# %cd darknet
# !sed -i 's/OPENCV=0/OPENCV=1/' Makefile
# !sed -i 's/GPU=0/GPU=1/' Makefile
# !sed -i 's/CUDNN=0/CUDNN=1/' Makefile
# !make


def compute_yolo_hyperparameters(num_classes: int) -> dict:
    """Berechnet die von der YOLOv3-Config abhängigen Werte für die Klassenzahl."""
    return {
        "filters": (num_classes + 5) * 3,
        "max_batches": max(num_classes * 2000, 6000),
    }


hyperparameters = compute_yolo_hyperparameters(len(CUSTOM_OBJECTS))
print(hyperparameters)

# 3 – YOLOv3-Config anpassen
# !cp cfg/yolov3.cfg cfg/yolov3_custom.cfg
# !sed -i 's/batch=1/batch=64/' cfg/yolov3_custom.cfg
# !sed -i 's/subdivisions=1/subdivisions=16/' cfg/yolov3_custom.cfg
# !sed -i f"s/max_batches = 500200/max_batches = {hyperparameters['max_batches']}/" cfg/yolov3_custom.cfg
# Klassen- und Filteranzahl in den drei YOLO-Layern anpassen
# (Zeilen 610, 696, 783 bzw. 603, 689, 776 in yolov3_custom.cfg)

# 4 – Datensatz vorbereiten
# !mkdir -p data/obj
# !unzip {DATASET_ARCHIVE} -d data/obj

objects_file_content = "\n".join(CUSTOM_OBJECTS)
# !echo -e "{objects_file_content}" > data/obj.names

images_list = sorted(glob.glob("data/obj/*.[jJ][pP][gG]") +
                      glob.glob("data/obj/*.[pP][nN][gG]") +
                      glob.glob("data/obj/*.[jJ][pP][eE][gG]"))
print(f"Gefundene Trainingsbilder: {len(images_list)}")

# train.txt erstellen
with open("data/train.txt", "w") as train_file:
    train_file.write("\n".join(images_list))

# 5 – Vortrainierte Gewichte herunterladen
# !wget https://pjreddie.com/media/files/darknet53.conv.74

# 6 – Training starten
# !./darknet detector train data/obj.data cfg/yolov3_custom.cfg darknet53.conv.74 -dont_show
