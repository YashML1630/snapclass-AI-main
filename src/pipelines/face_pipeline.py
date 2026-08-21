import dlib
import numpy as np
import face_recognition_models
import streamlit as st

from src.database.db import get_all_students


# ============================================================
# LOAD DLIB MODELS
# ============================================================

@st.cache_resource
def load_dlib_models():
    detector = dlib.get_frontal_face_detector()

    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )

    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )

    return detector, sp, facerec


# ============================================================
# GET FACE EMBEDDINGS FROM IMAGE
# ============================================================

def get_face_embeddings(image_np):
    detector, sp, facerec = load_dlib_models()

    # Make sure image is uint8
    image_np = np.asarray(image_np, dtype=np.uint8)

    faces = detector(image_np, 1)

    encodings = []

    for face in faces:
        shape = sp(image_np, face)

        face_descriptor = facerec.compute_face_descriptor(
            image_np,
            shape,
            1
        )

        encodings.append(
            np.array(face_descriptor, dtype=np.float64)
        )

    return encodings


# ============================================================
# LOAD REGISTERED STUDENT EMBEDDINGS
# ============================================================

def get_registered_students():
    student_db = get_all_students()

    if not student_db:
        return []

    registered_students = []

    for student in student_db:

        embedding = student.get("face_embedding")

        if embedding is None:
            continue

        if len(embedding) == 0:
            continue

        try:
            embedding = np.array(
                embedding,
                dtype=np.float64
            )

            # Face embedding should contain 128 values
            if embedding.shape[0] != 128:
                continue

            registered_students.append({
                "student_id": int(student["student_id"]),
                "embedding": embedding
            })

        except Exception:
            continue

    return registered_students


# ============================================================
# PREDICT ATTENDANCE
# ============================================================

def predict_attendance(class_image_np):

    # Detect faces in classroom image
    encodings = get_face_embeddings(class_image_np)

    detected_student = {}

    # Load registered students
    registered_students = get_registered_students()

    if not registered_students:

        return (
            detected_student,
            [],
            len(encodings)
        )

    all_students = sorted(
        list(
            set(
                student["student_id"]
                for student in registered_students
            )
        )
    )

    # ========================================================
    # COMPARE EVERY DETECTED FACE
    # WITH EVERY REGISTERED FACE
    # ========================================================

    for encoding in encodings:

        best_student_id = None
        best_distance = float("inf")

        for student in registered_students:

            registered_embedding = student["embedding"]

            distance = np.linalg.norm(
                registered_embedding - encoding
            )

            if distance < best_distance:

                best_distance = distance
                best_student_id = student["student_id"]

        # ====================================================
        # IMPORTANT:
        # Unknown faces must NOT be assigned to anybody.
        # ====================================================

        RECOGNITION_THRESHOLD = 0.55

        if (
            best_student_id is not None
            and best_distance <= RECOGNITION_THRESHOLD
        ):

            detected_student[best_student_id] = {
                "distance": float(best_distance)
            }

    return (
        detected_student,
        all_students,
        len(encodings)
    )