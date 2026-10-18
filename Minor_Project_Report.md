# MINOR PROJECT REPORT

## Digital Facial Recognition Attendance System

Submitted in partial fulfilment of the requirements for  
**[Course / Diploma / Degree Name]**

**Submitted by**  
Student Name: [Your Name]  
Enrollment No.: [Your Enrollment Number]  
Class / Branch: [Class and Branch]

**Under the guidance of**  
[Guide Name]

**[College Name]**  
[Department Name]  
Academic Year: [20__–__]

---

# Certificate

This is to certify that the minor project report entitled **“Digital Facial Recognition Attendance System”** is submitted by **[Your Name]**, Enrollment No. **[Your Enrollment Number]**, of **[Class / Branch]**, **[College Name]**, in partial fulfilment of the requirements for **[Course / Diploma / Degree Name]**.

The work described in this report has been carried out by the student under my guidance during the academic year **[20__–__]**. To the best of my knowledge, this report is an original academic submission by the student.

|  |  |
|---|---|
| Project Guide | Head of Department |
| Name: [Guide Name] | Name: [HOD Name] |
| Signature: ____________________ | Signature: ____________________ |
| Date: _________________________ | Date: _________________________ |

**Place:** [City / Town]  
**College seal**

---

# Declaration

I, **[Your Name]**, Enrollment No. **[Your Enrollment Number]**, declare that this report titled **“Digital Facial Recognition Attendance System”** is prepared by me as part of the minor project work for **[Course / Diploma / Degree Name]** at **[College Name]**.

The work presented in this report was completed under the guidance of **[Guide Name]**. Sources used for technical information are listed in the References section. I have not knowingly presented another person's work as my own.

**Student Name:** [Your Name]  
**Signature:** ____________________  
**Date:** _________________________  
**Place:** [City / Town]

---

# Acknowledgement

I express my sincere thanks to **[Guide Name]** for providing guidance, suggestions, and support during this project. The guidance helped me understand the project requirements and organise the work.

I am grateful to the Head of Department, **[HOD Name]**, and the faculty members of **[Department Name]**, **[College Name]**, for their encouragement and for providing the academic facilities required for this project.

I also thank my classmates, friends, and family members for their help and encouragement. Finally, I acknowledge the authors and maintainers of the software tools and documentation referred to while studying this subject.

---

# Abstract / Synopsis

The **Digital Facial Recognition Attendance System** is a project intended to make classroom attendance recording quicker and more organised. In a manual process, an instructor calls each student's name or passes around an attendance sheet. This can take time, and the resulting records may need to be entered into a computer later.

The proposed system uses a camera to capture a face and a recognition process to compare it with enrolled student data. When a student is recognised, the system can record an attendance entry with the student's identity and the date and time. A staff member can then review the resulting records. The system is intended to assist attendance-taking; a staff member remains responsible for checking records and handling cases where recognition is unsuccessful.

The project is planned as a web-based application. The project name and available README identify the purpose as student attendance using face recognition. The source files needed to confirm the precise framework, recognition library, data storage, and run command were not present in the reviewed project folder. Therefore, implementation-specific items in this report are marked for confirmation before final submission. Replace those notes with the technologies and behaviour actually used in the completed project.

**Keywords:** attendance, face recognition, student records, camera, automation

---

# Table of Contents

1. Title Page
2. Certificate
3. Declaration
4. Acknowledgement
5. Abstract / Synopsis
6. Table of Contents
7. Chapter 1: Introduction
8. Chapter 2: Project Description
9. Chapter 3: Project Flow
10. Chapter 4: Project Features
11. Chapter 5: Technologies Used
12. Chapter 6: Project Demo Video
13. Chapter 7: How to Use This Project
14. Chapter 8: Advantages and Limitations
15. Chapter 9: Future Scope
16. Chapter 10: Conclusion
17. References
18. Suggested Screenshots

*Update page numbers after formatting this document in a word processor.*

---

# Chapter 1: Introduction

## 1.1 Background of the Project

Attendance is an important part of classroom administration. It helps an institution record student participation, prepare reports, and identify attendance trends. A paper register is easy to start using, but calling names and transferring records to electronic files can take time.

Computer vision makes it possible for software to analyse images captured by a camera. Facial recognition systems use image-processing techniques to compare a face in a new image with previously enrolled face data. When used carefully in an attendance application, this can provide an alternative way to record a student's presence.

This project applies that idea to student attendance. Its intended workflow is to enrol student information, capture a face during an attendance session, identify a matching student, and save an attendance record for review.

## 1.2 Problem Statement

Manual attendance can consume class time and requires records to be maintained consistently. Handwritten entries may be difficult to search, summarise, or transfer into reports. A digital system can help organise these records and reduce repeated manual entry.

The project addresses the following problem:

> How can a classroom attendance record be captured and organised using a camera and facial recognition, while allowing staff to review and correct the result?

Recognition is not guaranteed to be correct in every environment. The system should therefore be treated as an aid and should provide a way for a responsible staff member to review its output.

## 1.3 Objectives

The main objectives of the project are:

- To provide a digital method for recording student attendance.
- To use a camera image as input for a face-recognition workflow.
- To associate a recognised face with the corresponding enrolled student.
- To record attendance with useful session information, such as a date and time, if supported by the implementation.
- To make saved attendance records easier to view and manage.
- To reduce repetitive work compared with recording and transcribing a paper register.
- To study the use of web technologies and computer-vision tools in an academic application.

## 1.4 Scope of the Project

The project is intended for a small academic setting, such as a classroom demonstration or a minor-project prototype. Its scope may include student enrolment, collecting face samples, running recognition, marking attendance, and displaying saved records, depending on the features implemented in the final version.

The project does not replace institutional attendance policy or staff supervision. It should not be used as the only evidence for a high-stakes decision without validation, consent, suitable security, and a manual review process. Recognition quality can vary with lighting, camera quality, face angle, and changes in appearance.

The final scope must match the features that are actually present in the submitted application. Remove any feature from this report that was not implemented.

---

# Chapter 2: Project Description

## 2.1 Project Overview

The Digital Facial Recognition Attendance System is designed as a user-facing application connected to a recognition and attendance-recording process. A camera supplies a live image or a captured frame. The recognition component analyses the face and attempts to match it to enrolled data. If a suitable match is found, the application can record the student's attendance.

The exact application architecture and storage method must be confirmed against the final code. A typical arrangement for this kind of project is:

1. **User interface:** Pages and controls for starting attendance or viewing records.
2. **Application logic:** Code that coordinates camera input, recognition, and attendance actions.
3. **Recognition component:** A computer-vision library or model that detects and compares faces.
4. **Student data:** Student names or identifiers linked to enrolled face samples or recognition data.
5. **Attendance records:** A file or database that stores attendance entries for later review.

These are functional roles, not a claim that each role exists as a separate module or that any particular library or database is used in the submitted code.

## 2.2 Main Modules

The following modules describe the intended system. Keep only the modules supported by the final implementation.

### A. Student Enrolment and Face Data

This module associates a student identifier and relevant student details with face data. An authorised operator should collect samples in suitable lighting and ensure that each sample belongs to the correct student.

### B. Camera Capture

This module obtains an image or video frame from a camera. The camera must be available to the device, and the user may need to allow browser or operating-system camera access.

### C. Face Detection and Recognition

This module locates a face in the captured image and compares it with enrolled data. It should handle the result as either a match, no match, or an unusable image. The specific algorithm and confidence threshold depend on the implemented library.

### D. Attendance Recording

When the recognition process identifies a student, the application records the attendance event. A useful record commonly contains a student identifier and date/time. The final report should state the actual fields and duplicate-attendance behaviour implemented by the project.

### E. Attendance Review

This module presents saved attendance information to an authorised user. Depending on the project, records may be displayed in a table or saved in a local file. Staff should verify records and resolve recognition errors using the institution's normal procedure.

### F. User Interface

The interface guides the user through the available actions, such as opening an attendance page, starting capture, viewing a result, and returning to a previous page. Labels and messages should make it clear whether the system has recognised a student or needs the user to try again.

## 2.3 How the System Works

At a high level, the system follows these stages:

1. Student identity and face data are prepared and enrolled.
2. A user opens the attendance function and starts the camera or image-capture process.
3. The system checks the captured input for a usable face.
4. The recognition process compares the detected face with enrolled data.
5. If a match is accepted, the system associates it with a student record.
6. An attendance entry is saved or presented for confirmation, according to the implementation.
7. The user can review the result and continue or end the session.

If no face is found or no match is accepted, the system should communicate that result rather than recording an incorrect identity. A staff member may then retry the capture or record attendance manually.

## 2.4 Data and Privacy Considerations

Face images and recognition data are sensitive personal information. The project should collect only the data needed for its academic purpose, obtain appropriate permission, restrict access, and avoid sharing samples publicly. The institution's rules should determine how long the data is retained and how it is securely removed.

For a demonstration, use authorised participants or clearly identified test data. Do not use the system to make consequential decisions without evaluating its accuracy and addressing consent, security, accessibility, and bias concerns.

---

# Chapter 3: Project Flow

## 3.1 Step-by-Step Working Flow

1. **Start the application:** The operator launches the project and opens its main page.
2. **Prepare student data:** Student details and permitted face samples are added or loaded.
3. **Open attendance:** The operator chooses the attendance function.
4. **Allow camera access:** The operator grants permission if the browser or device asks for it.
5. **Capture an image:** The camera supplies an image or frame to the application.
6. **Check the face:** The system determines whether the input contains a usable face.
7. **Compare the face:** The recognition component compares the face with enrolled data.
8. **Handle the result:** A match is shown to the operator; an unknown or unclear face prompts another capture or manual handling.
9. **Save attendance:** The application records the event if the recognition result is accepted and the implementation supports saving.
10. **Review and finish:** The operator reviews the displayed result or attendance list and ends the session.

## 3.2 Text Flow Diagram

```text
+------------------+
| Start application|
+--------+---------+
         |
         v
+--------------------------+
| Load/enrol student data  |
+------------+-------------+
             |
             v
+--------------------------+
| Open attendance function|
+------------+-------------+
             |
             v
+--------------------------+
| Capture image from camera|
+------------+-------------+
             |
             v
+--------------------------+
| Is a usable face found?  |
+--------+------------+----+
         | Yes        | No
         v            v
+----------------+  +----------------------+
| Compare with   |  | Show message and      |
| enrolled data  |  | ask for another image|
+-------+--------+  +----------+-----------+
        |                      |
        v                      +----> Capture again
+--------------------------+
| Is an identity accepted? |
+--------+------------+----+
         | Yes        | No
         v            v
+------------------+  +----------------------+
| Record attendance|  | Show no-match result |
+--------+---------+  | and allow retry/manual|
         |            | attendance procedure |
         v            +----------------------+
+--------------------------+
| Review result / continue |
+------------+-------------+
             |
             v
       +-----------+
       |    End    |
       +-----------+
```

## 3.3 User Actions and System Responses

| User action | Expected system response |
|---|---|
| Opens the application | Displays the available project functions. |
| Selects attendance | Opens the attendance interface or capture process. |
| Grants camera access | Enables image capture, if camera capture is implemented. |
| Presents a face to the camera | Attempts face detection and recognition. |
| Is recognised | Shows the associated student identity and records or prepares an attendance entry. |
| Is not recognised | Shows a no-match or retry message; the system should not silently assign another identity. |
| Opens attendance records | Displays saved records, if that view is implemented. |
| Ends the session | Stops capture or returns to the previous screen. |

---

# Chapter 4: Project Features

The features below describe the intended project. Confirm each against the completed software before claiming it as implemented.

## 4.1 Digital Attendance

The application is intended to record attendance electronically rather than relying only on a paper register. This can make records easier to organise and review.

## 4.2 Face-Based Identification

The recognition workflow attempts to associate a captured face with enrolled student data. The result depends on the quality of the image and the recognition method.

## 4.3 Student Data Association

Face data is linked to a student identity so that an accepted recognition result can be attributed to the correct person. Student identifiers should be used consistently to avoid confusion between records.

## 4.4 Camera or Image Capture

The system can receive an image for processing through a camera or another input method. The actual input method should be described as implemented, and camera permission requirements should be explained to users.

## 4.5 Attendance Record Review

An electronic record can be presented for review after attendance is marked. If the application includes a searchable or downloadable list, describe its supported filters and output format here.

## 4.6 Recognition Feedback

Clear messages help users understand whether a face was detected, recognised, or rejected. Useful feedback also makes it easier to retry when the image is unclear.

## 4.7 Manual Review

Human review is important when a face cannot be recognised or a result appears incorrect. A staff member should be able to follow the normal attendance procedure rather than depending entirely on an automated result.

---

# Chapter 5: Technologies Used

> **Important:** The project folder available for preparing this report identifies the project purpose but does not include the application source or dependency list. The table below is a fill-in guide, not verification of the technologies used. Replace each entry with the exact tools used in the final build and remove tools that do not apply.

| Technology | Role in the project | Confirmation required |
|---|---|---|
| Python | May be used for application logic, data handling, and connecting the interface to recognition functions. | Confirm from source files. |
| Flask or another web framework | May serve web pages and handle application requests. | Confirm the framework and version. |
| HTML | Defines the structure of web pages and forms. | Confirm from the templates. |
| CSS | Styles page layout, controls, and visual feedback. | Confirm from stylesheet files. |
| JavaScript | Adds client-side interactions and may manage camera controls or page actions. | Confirm from script files. |
| OpenCV or another computer-vision library | May provide image capture, image processing, or face-detection functions. | Confirm the exact library and features used. |
| Face-recognition model/library | Compares face data to determine whether a student matches an enrolled identity. | State the actual model/library and its configuration. |
| CSV, database, or other storage | May store student information and attendance entries. | State the actual storage format and fields. |
| Web browser and camera | Provide the user interface and, where supported, image input. | State tested browsers and camera requirements. |

## 5.1 Technology Selection Rationale

For a web-based prototype, web technologies can provide a user interface that runs in a browser. A server-side language can coordinate requests and data handling, while a computer-vision library can process images. Local file or database storage can make records available for review.

The selected technology should match the actual implementation and the available hardware. Performance and recognition quality depend on the model, camera, machine, lighting, and the number and quality of enrolled samples. Do not report a framework or algorithm as used unless it appears in the project code or dependency documentation.

---

# Chapter 6: Project Demo Video

## 6.1 Demo Video Script (Approximately 2–3 Minutes)

| Time | What to show on screen | Voice-over narration |
|---|---|---|
| 0:00–0:15 | Display the project title and a view of the application. | “Hello. This is my minor project, the Digital Facial Recognition Attendance System. It is designed to support classroom attendance using face recognition and digital records.” |
| 0:15–0:35 | Show the main page and point out the available functions. | “The application provides access to its main attendance functions. The exact options shown here are the features included in this project build.” |
| 0:35–0:55 | Show the student-enrolment or prepared test-data screen, if implemented. Do not reveal real personal data. | “Before attendance can be recorded, the system needs student information and permitted face samples. For this demonstration, I am using authorised test data.” |
| 0:55–1:20 | Open the attendance page and show the camera permission prompt or capture view. | “I will now open the attendance function. If the browser requests camera permission, the user must allow it for image capture to work.” |
| 1:20–1:45 | Capture a test face and show the recognition result. | “The system analyses the captured image and compares the face with enrolled data. When it accepts a match, the associated student identity is displayed.” |
| 1:45–2:05 | Show the attendance result or saved record, if supported. | “The attendance result can then be saved or reviewed, depending on the project configuration. The staff member should verify the record.” |
| 2:05–2:25 | Demonstrate an unknown/unclear face result or show the relevant message. | “If the system cannot find a suitable match, it should report that clearly. The user can try again or follow the institution’s manual attendance procedure.” |
| 2:25–2:40 | Show the closing screen or return to the main page. | “This project demonstrates how a camera-based recognition workflow can support attendance management. Thank you.” |

**Recording reminders:** Use test data or obtain permission from participants. Hide personal information and avoid showing private face datasets or credentials. If a listed screen or behaviour is not implemented, replace that segment with a screen that exists in the final application.

---

# Chapter 7: How to Use This Project

## 7.1 Installation and Setup

The exact setup command cannot be confirmed from the available project files because the application entry point and dependency manifest were not included. Before submitting this chapter, fill in the actual filenames and commands from the final source. Do not run guessed commands on the submission machine.

1. Copy or clone the completed project source to a supported computer.
2. Install the language runtime and dependencies listed by the project.  
   **Runtime/version:** [Enter the tested runtime and version.]  
   **Dependency installation command:** [Enter the verified command.]
3. Connect or enable a camera if the application uses live capture.
4. Check that the required student data and recognition resources are available.
5. Configure any local settings required by the project. Do not include passwords, private keys, or real student face data in the report.
6. Start the application using its verified entry point.  
   **Run command:** [Enter the exact command.]  
   **Local address, if applicable:** [Enter the address shown by the running application.]
7. Open the application in a supported browser if it is web-based.

## 7.2 Using the Main Functions

### A. Open the Application

1. Start the application using the verified command above.
2. Open the local address in a browser if the project launches a web interface.
3. Check that the main page loads without an error.

### B. Prepare Student Data

1. Open the student-enrolment function, if available.
2. Enter the required student identifier and details.
3. Capture or add face samples only with the participant's permission.
4. Verify that the sample is associated with the correct student.

### C. Mark Attendance

1. Select the attendance function.
2. Allow camera access if prompted.
3. Position the face in view of the camera with adequate lighting.
4. Wait for the system response.
5. Check the displayed identity before relying on the result.
6. If the system reports no match or an unclear image, retry or use the approved manual procedure.

### D. Review Attendance

1. Open the attendance records function, if implemented.
2. Select the available date, class, or other filter, if supported.
3. Check the records for missing or incorrect entries.
4. Export or save the records only using the application's supported function.

### E. End the Session

1. Stop camera capture using the application's control, if available.
2. Close the page or stop the server using the method documented with the code.
3. Keep student and face data in the approved secure location.

---

# Chapter 8: Advantages and Limitations

## 8.1 Advantages

- **Can reduce repeated manual entry:** A recognition result may help record attendance without calling every name.
- **Electronic records are easier to organise:** Digital entries can be reviewed and processed more easily than handwritten sheets, depending on the storage format.
- **Demonstrates practical computer vision:** The project combines image input with a real administrative use case.
- **Provides immediate feedback:** A user can see whether the system found a match and retry when needed.
- **Can be extended:** Additional functions such as summaries, reports, or role-based access may be added in future versions.

## 8.2 Limitations

- **Recognition can fail:** Poor lighting, camera quality, face angle, occlusion, and changes in appearance can affect results.
- **Incorrect matches are possible:** A recognition system should not be treated as infallible; human review is required.
- **Camera and hardware are required:** Performance depends on camera availability and the processing capability of the device.
- **Face data creates privacy responsibilities:** The project must obtain suitable permission and protect stored samples and records.
- **The current project may be a prototype:** It may not include production-grade security, backups, auditing, or a deployment setup.
- **Platform support may be limited:** The project may rely on particular software versions or a local environment.
- **Setup depends on the actual implementation:** Users need accurate dependency and run instructions from the completed source code.

---

# Chapter 9: Future Scope

The project can be improved in the following ways:

1. **Improve recognition reliability:** Evaluate the system under different lighting conditions and camera positions, then tune or replace the recognition method where appropriate.
2. **Add secure user accounts:** Provide authorised access for staff and administrators, with permissions suited to each role.
3. **Use a managed database:** Store student details and attendance records in a database with backup and recovery procedures.
4. **Add attendance reports:** Generate daily, weekly, or monthly summaries and export them in a suitable format.
5. **Support manual correction:** Allow authorised staff to correct an error while recording who made the change.
6. **Protect personal data:** Add secure storage, access controls, retention rules, and a clear deletion process for face data.
7. **Improve accessibility and usability:** Provide clear instructions, keyboard support, readable messages, and alternatives for users who cannot use face recognition.
8. **Test fairness and accuracy:** Measure false matches and missed matches across varied participants and conditions before broader use.
9. **Support more devices:** Test responsive pages and compatible cameras on different computers and browsers.
10. **Provide operational monitoring:** Record application errors and system health without logging sensitive face images or unnecessary personal information.

---

# Chapter 10: Conclusion

The Digital Facial Recognition Attendance System is a minor project that explores the use of facial recognition to support classroom attendance. Its intended process links student enrolment, image capture, recognition, attendance recording, and review. By organising attendance information digitally, the project can demonstrate a practical application of web development and computer vision.

The project also illustrates important limitations. Recognition may be affected by image quality and environmental conditions, and face data requires careful handling. Therefore, an automated result should be reviewed by a responsible staff member, and an alternative attendance method should remain available.

This report describes the project at a functional level. Before final submission, the student should replace all bracketed fields, confirm each technology and feature against the final source code, add actual setup commands, and remove any module that is not implemented.

---

# References

1. OpenCV, “OpenCV Documentation.” Available at: https://docs.opencv.org/ (accessed [insert date]).
2. Python Software Foundation, “Python Documentation.” Available at: https://docs.python.org/3/ (accessed [insert date]).
3. Flask, “Flask Documentation.” Available at: https://flask.palletsprojects.com/ (accessed [insert date]). Include only if Flask is used.
4. MDN Web Docs, “HTML, CSS, and JavaScript Documentation.” Available at: https://developer.mozilla.org/ (accessed [insert date]). Include only the technologies used.
5. [Name of actual face-recognition library or model], [title of official documentation], [URL] (accessed [insert date]).
6. [Project repository or course material], [title or URL], [accessed date]. Include sources actually used.

---

# Suggested Screenshots to Add Manually

1. Main page or home screen.
2. Student enrolment or test-data preparation screen.
3. Camera permission or camera capture screen (use authorised test data).
4. Successful recognition result.
5. No-match or retry message.
6. Attendance records view.
7. Example attendance output file or report, with personal details hidden.
8. Application running in the browser or terminal, with private paths and credentials hidden.

**Before submission:** Replace every bracketed field, verify the stack and setup instructions from the final project source, confirm certificate wording with the college, update the table of contents and page numbers after formatting, and add only genuine screenshots from your application.
