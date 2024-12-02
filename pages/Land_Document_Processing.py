import tempfile
from typing import List
import streamlit as st
from modules.document_processing import DocumentProcessor, logger
from modules.data_storage import Storage


# def store_data():
#     """Store processed documents in storage and display a summary."""
#     storage = Storage()
#     success_uploads: List[dict] = []
#     failed_uploads: List[dict] = []

#     # Retrieve processed documents from session state
#     processed_docs: List[dict] = st.session_state.get("processed_docs", [])

#     for index, doc in enumerate(
#         processed_docs.copy()
#     ):  # Iterate over a copy to safely modify the list
#         response = storage.store_data(doc)
#         if response:
#             success_uploads.append(response)
#             processed_docs.remove(doc)  # Remove successfully stored document
#         else:
#             failed_uploads.append({"id": index, "document": doc})
#             st.warning(f"Failed to save document at index {index}")

#     # Update session state
#     st.session_state["processed_docs"] = processed_docs

#     # Display Summary
#     st.write("### Save Summary")
#     st.write(f"- **Success:** {len(success_uploads)}")
#     st.write(f"- **Failed:** {len(failed_uploads)}")
#     if failed_uploads:
#         st.write("Details of failed uploads:")
#         for failed in failed_uploads:
#             st.json(failed)


# Initialize the DocumentProcessor
processor = DocumentProcessor(llm_api_key="your-api-key")

# App Title
st.title("Document Processing App")

# Sidebar Instructions
st.sidebar.header("Instructions")
st.sidebar.markdown(
    """
1. Upload images or documents (PDF, JPG, PNG).
2. Click **Process** to process the documents.
3. View results in the output section.
4. Save processed data using the **Save Processed Data** button.
"""
)

# File Uploader
uploaded_files = st.file_uploader(
    "Upload your documents (PDF, JPG, PNG)",
    type=["pdf", "jpg", "png"],
    accept_multiple_files=True,
)

model = st.selectbox(label="Model", options=["GEMINI", "OPENAI"])

# Process Documents
if uploaded_files:
    st.write("### Uploaded Documents")
    for file in uploaded_files:
        st.write(f"- {file.name}")

    if st.button("Process"):
        st.write("Processing documents... Please wait.")
        processed_docs = st.session_state.get("processed_docs", [])

        for file in uploaded_files:
            try:
                # Save file temporarily
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".tmp")
                with open(temp_file.name, "wb") as f:
                    f.write(file.read())

                # Process the document
                result = processor.process_document(temp_file.name, file.name, model)

                if result:
                    # st.session_state["results_tt"] = result.data["results"]
                    # st.write(st.session_state["results_tt"])
                    processed_docs.append(result.data["results"])
                    st.success(f"Successfully processed {file.name}")
                    # if "image" in result.data:
                    #     st.image(result.data["image"])
                    if "results" in result.data:
                        st.write(result.data["results"]["plot_info"])
                else:
                    st.error(f"Failed to process {file.name}: {result.error}")

            except Exception as e:
                st.error(f"An error occurred while processing {file.name}: {e}")

        # Update session state with processed documents
        st.session_state["processed_docs"] = processed_docs

else:
    st.info("Please upload documents to begin processing.")

# Save Processed Data Button
if st.session_state.get("processed_docs"):
    if st.button("Save Processed Data", key="save_data"):
        """Store processed documents in storage and display a summary."""
        storage = Storage()
        success_uploads: List[dict] = []
        failed_uploads: List[dict] = []

        # Retrieve processed documents from session state
        processed_docs: List[dict] = st.session_state.get("processed_docs", [])
        processed_docs = [doc for doc in processed_docs if "point_list" in doc]

        for index, doc in enumerate(
            processed_docs
        ):  # Iterate over a copy to safely modify the list
            if len(doc["point_list"]) > 0:
                response = storage.store_data(doc)
                if response:
                    success_uploads.append(doc)
                    processed_docs.remove(doc)  # Remove successfully stored document
                else:
                    failed_uploads.append({"id": index, "document": doc})
                    st.warning(f"Failed to save document at index {index}")
            else:
                failed_uploads.append({"id": index, "document": doc})
                st.warning("Failed to save document because point_list is empty.")

        # Update session state
        st.session_state["processed_docs"] = processed_docs

        # Display Summary
        st.write("### Save Summary")
        st.write(f"- **Success:** {len(success_uploads)}")
        st.write(f"- **Failed:** {len(failed_uploads)}")
        if failed_uploads:
            st.write("Details of failed uploads:")
            for failed in failed_uploads:
                st.json(failed["document"]["plot_info"])
