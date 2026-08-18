import streamlit as st
from src.database.db import enroll_student_to_subject
from src.database.config import supabase
import time
@st.dialog("Enroll in subject")
def enroll_dialog(join_code = None):
    st.write("Enter the subject code provided by your teacher to enroll")
    if join_code:
        join_code = join_code.strip().upper()
        st.info(f"Joining subject: {join_code}")
    else:
        join_code = st.text_input(
            'subject_code',
            placeholder='e.g. CS101'
        )

    if st.button('Enrol now',type='primary',width='stretch'):
        if join_code:
            res = supabase.table('subjects').select('subject_id,name,subject_code').eq('subject_code',join_code).execute()
            if res.data:
                subject = res.data[0]
                student_id = st.session_state.student_data['student_id']
                check = supabase.table('subject_students').select('*').eq('subject_id',subject['subject_id']).eq('student_id',student_id).execute()
                if check.data:
                    st.warning('You are already enrolled in these program')
                else:
                    enroll_student_to_subject(student_id,subject['subject_id'])
                    st.success('Succesfully enrolled !')
                    time.sleep(1)
                    st.rerun()
        else:
            st.warning('Please enter subject code')