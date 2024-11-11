import streamlit as st

def setup_page_config():
    st.set_page_config(
        page_title="4th-ir POC Repo",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

def load_css():
    # External CSS dependencies
    st.markdown(
        """
        <link href="https://cdnjs.cloudflare.com/ajax/libs/mdbootstrap/4.19.1/css/mdb.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
        <link rel="icon" href="https://www.4th-ir.com/favicon.ico">
        <!-- Primary Meta Tags -->
<title>4thir-POC-repo</title>
<meta name="title" content="4thir-POC-repo" />
<meta name="description" content="view our proof of concepts" />

<!-- Open Graph / Facebook -->
<meta property="og:type" content="website" />
<meta property="og:url" content="https://4thir-poc-repositoty.streamlit.app/" />
<meta property="og:title" content="4thir-POC-repo" />
<meta property="og:description" content="view our proof of concepts" />
<meta property="og:image" content="https://www.4th-ir.com/favicon.ico" />

<!-- Twitter -->
<meta property="twitter:card" content="summary_large_image" />
<meta property="twitter:url" content="https://4thir-poc-repositoty.streamlit.app/" />
<meta property="twitter:title" content="4thir-POC-repo" />
<meta property="twitter:description" content="view our proof of concepts" />
<meta property="twitter:image" content="https://www.4th-ir.com/favicon.ico" />

<!-- Meta Tags Generated with https://metatags.io -->
        """,
        unsafe_allow_html=True
    )

    # Custom CSS to hide Streamlit components and adjust layout
    st.markdown(
        """
        <style>
            header {visibility: hidden;}
            .main {
                margin-top: -20px;
                padding-top: 10px;
            }
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .navbar {
                padding: 1rem;
                margin-bottom: 2rem;
            }
            .card {
                padding: 1rem;
                margin-bottom: 1rem;
                transition: transform 0.2s;
                border-radius:5px;
            }
            .card:hover {
                transform: scale(1.02);
            }
            .navbar-brand img {
                margin-right: 10px;
                height: 30px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

def create_navbar():
    st.markdown(
        """
        
        <nav class="navbar fixed-top navbar-expand-lg navbar-dark" style="background-color: #4267B2;">
            <a class="navbar-brand" href="#" target="_blank">
                <img src="https://www.4th-ir.com/favicon.ico" alt="4th-ir logo">
                4th-ir POC Repo
            </a>
        </nav>

        <div class="card card-success alert-success"><marquee>Check Sidebar for Projects</marquee></div>
        """,
        unsafe_allow_html=True
    )

def create_project_card(project_name, color_class, target="_parent"):
    return f"""
   
        <a href='{project_name}' class='card alert {color_class}' target='{target}' style='text-decoration: none; color: black;'>
            <h5 class='card-title'>{project_name}</h5>
        </a>
    
    """

def main():
  
    setup_page_config()
    
  
    load_css()
    create_navbar()
    
    
    projects = {
        "Age-Detection": "alert-success",
        "Hand-Written-Text-Detector": "alert-warning",
        "Loan-Document-Analyzer": "alert-info",
        "Medical-doc-analyzer": "alert-danger",
        "Ride-router" :"alert  btn-warning",
        "Self-organization-maps" :"alert  btn-success",
        "google-maps" :"alert  btn-info",
    }
    

    for i in range(0, len(projects), 2):
        col1, col2 = st.columns(2)
        
    
        items = list(projects.items())[i:i+2]
        
        # Add cards to columns
        if len(items) > 0:
            col1.markdown(
                create_project_card(items[0][0], items[0][1]),
                unsafe_allow_html=True
            )
        
        if len(items) > 1:
            col2.markdown(
                create_project_card(items[1][0], items[1][1]),
                unsafe_allow_html=True
            )

if __name__ == "__main__":
    main()