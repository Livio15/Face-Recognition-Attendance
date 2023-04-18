import math
import pickle
import os
import face_recognition
from sklearn import neighbors

path = 'dataset'

clf = None
def getImagesAndLabels(path):
    global clf

    ids = [id for id in os.listdir(path)]
    encodings = []
    labels = []

    for idx, id in enumerate(ids):
        id_img_paths = [os.path.join(path, id, img_path)
                        for img_path in os.listdir(os.path.join(path, id))]

        for id_img_path in id_img_paths:
            img = face_recognition.load_image_file(id_img_path)
            face_bounding_boxes = face_recognition.face_locations(img)

            if len(face_bounding_boxes) == 1:
                face_enc = face_recognition.face_encodings(img)[0]

                encodings.append(face_enc)
                labels.append(id)
            else:
                print(
                    f"{id_img_path} không thể dùng để train vì không tìm thấy mặt hoặc nhiều hơn 1 khuôn mặt")

    clf = neighbors.KNeighborsClassifier(n_neighbors=int(
        round(math.sqrt(len(encodings)))), algorithm='ball_tree', weights='distance')
    clf.fit(encodings, labels)


getImagesAndLabels(path)

with open("trained_knn_model.clf", 'wb') as f:
    pickle.dump(clf, f)