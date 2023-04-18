import math, dlib
import pickle
import os, cv2
import face_recognition
from sklearn import neighbors

clf = None

with open("trained_knn_model.clf", 'rb') as f:
    clf = pickle.load(f)

video_capture = cv2.VideoCapture(0)
process_this_frame = True
while True:
    ret, frame = video_capture.read()

    if process_this_frame:
        small_frame = dlib.resize_image(frame, 0.25)
        face_locations = face_recognition.face_locations(small_frame)
        face_encodings = face_recognition.face_encodings(
            small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:

            isMatched = clf.kneighbors([face_encoding], n_neighbors=1)[
                0][0][0] < 0.6
            name = clf.predict([face_encoding])
            face_names.append(name[0] if isMatched else 'unknown')

    process_this_frame = not process_this_frame

    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        cv2.rectangle(frame, (left, bottom - 35),
                      (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6),
                    font, 1.0, (255, 255, 255), 1)

    cv2.imshow('Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()