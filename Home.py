import streamlit as st


def setup_page_config():
    st.set_page_config(
        page_title="4th-ir POC Repo",
        page_icon="https://www.4th-ir.com/favicon.ico",
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def load_css():
    # External CSS dependencies
    st.markdown(
        """
        <meta charset="UTF-8">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/mdbootstrap/4.19.1/css/mdb.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
        <link rel="icon" href="https://www.4th-ir.com/favicon.ico">
        
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

        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        """,
        unsafe_allow_html=True,
    )

    # Custom CSS to hide Streamlit components and adjust layout
    st.markdown(
        """
        <style>
        /* Hide the Streamlit header and menu */
        header {visibility: hidden;}
                /* Optionally, hide the footer */
                .streamlit-footer {display: none;}
                /* Hide your specific div class, replace class name with the one you identified */
                .st-emotion-cache-uf99v8 {display: none;}


        .hero-section {
            background: white;
            text: white;
            padding: 0rem 0;
            width: 0%;
            height:2px;
        }
        .feature-icon {
            width: 4rem;
            height: 4rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: white;
            box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
        }
        .card {
            transition: box-shadow 0.3s ease;
        }
        .card:hover {
            box-shadow: 0 1rem 3rem rgba(0,0,0,0.175);
        }
         .project-card {
            border-radius: 12px;
            border-left: 4px solid #0d6efd;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .project-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        .project-icon {
            width: 48px;
            height: 48px;
            background: rgba(13, 110, 253, 0.1);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1rem;
        }
        .project-meta {
            font-size: 0.875rem;
            color: #6c757d;
        }
      
        .nav-link {
            font-weight: 500;
            padding: 0.5rem 1rem !important;
        }
        .nav-links {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        @media (max-width: 768px) {
            .navbar .container {
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }
            .nav-links {
                flex-direction: column;
                align-items: flex-start;
                width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def create_navbar():
    st.html(
        """
             
        <nav class="navbar fixed-top navbar-expand-lg navbar-dark bg-white text-bold shadow-sm">
            <a class="navbar-brand text-primary" href="#" target="_blank">
                <img src="https://www.4th-ir.com/favicon.ico" alt="4th-ir logo">
                4th-ir POC Repo
            </a>
        </nav>

        <div class="hero-section">
            <div class="container text-center">
                <h1 class="display-4 text-white mb-3">4th-IR POC Page</h1>
                <!--<p class="lead text-white">Exploring the future of AI through innovative applications</p>-->
            </div>
        </div>
        
    <div id="projects">
    </div>

    
        """
    )


# def create_hero_section():
#     st.html(
#         """
#    <!-- Hero Section -->
#     <div class="hero-section">
#         <div class="container text-center">
#             <h1 class="display-4 text-white mb-3">4th-IR POC Page</h1>
#             <p class="lead text-white">Exploring the future of AI through innovative applications</p>
#         </div>
#     </div>
#     <div id="projects">
#     </div>
#       """
#     )


def create_project_card(project_name, details, target="_blank"):
    return f"""
    <div class="p-2" data-aos="fade-up" data-aos-delay="200">
        <div class="card project-card h-100 border-0 shadow-sm p-4">
            <div class="card-body">
                <div class="project-icon">
                    <svg width="24" height="24" fill="none" stroke="#0d6efd" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                    </svg>
                </div>
                <h5 class="card-title mb-3">{project_name}</h5>
                <div class="project-meta mb-3">
                    <span class="me-3">
                        <svg class="me-1" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="display: inline-block; vertical-align: -0.125em;">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        Updated recently
                    </span>
                    <span>
                        <svg class="me-1" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="display: inline-block; vertical-align: -0.125em;">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                        </svg>
                        Active
                    </span>
                </div>
                <p class="card-text mb-4">{details["description"]}</p>
                <a href='{project_name}' target='{target}' class="btn btn-primary text-white px-4">
                    View Project
                    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="display: inline-block; vertical-align: -0.125em; margin-left: 0.5rem;">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/>
                    </svg>
                </a>
            </div>
        </div>
    </div>
    """


def main():
    setup_page_config()
    load_css()
    create_navbar()
    # create_hero_section()

    projects = {
        "Age-Detection": {
            "color": "alert-success",
            "description": "A state-of-the-art age detection model that estimates user age with high accuracy from images and data inputs. This solution enhances identity verification, personalization, and demographic analytics, enabling more targeted and secure customer interactions.",
            "image": "https://www.4th-ir.com/favicon.ico",
        },
        "Hand-Written-Text-Detector": {
            "color": "alert-warning",
            "description": "An AI-driven tool for detecting and converting handwritten text into digital form, streamlining data entry and enabling efficient processing in sectors where physical documents are common, such as healthcare and education.",
            "image": "https://www.4th-ir.com/favicon.ico",
        },
        "Loan-Document-Analyzer": {
            "color": "alert-info",
            "description": "A machine learning solution designed to analyze and extract critical information from loan documents. It automates the review process, improving speed and compliance while reducing the risk of human error in loan processing.",
            "image": "https://www.4th-ir.com/favicon.ico",
        },
        "Medical-doc-analyzer": {
            "color": "alert-danger",
            "description": "An AI solution that analyzes medical documents to identify key clinical information quickly, supporting healthcare professionals in providing timely and accurate patient care, while optimizing document handling.",
            "image": "https://www.4th-ir.com/favicon.ico",
        },
        "Ride-router": {
            "color": "alert btn-warning",
            "description": "A route optimization platform for ride-sharing services, designed to ensure efficient route planning. It minimizes travel times, reduces fuel costs, and enhances customer satisfaction through optimized service delivery.",
            "image": "https://www.4th-ir.com/favicon.ico",
        },
        "Self-organization-maps": {
            "color": "alert btn-success",
            "description": "A tool that uses self-organizing maps for clustering and visualization, useful in data mining applications. It provides insights into large datasets by organizing and grouping similar data, aiding in pattern recognition and data interpretation.",
            "image": "https://www.4th-ir.com/favicon.ico",
        },
        "google-maps": {
            "color": "alert btn-info",
            "description": "An integrated Google Maps API solution, enhancing applications with powerful mapping features for route planning, location visualization, and geolocation services for a seamless user experience.",
            "image": "https://www.4th-ir.com/favicon.ico",
        },
        "Accent-recognition": {
            "color": "alert btn-danger",
            "description": "A sophisticated model for recognizing and classifying accents in speech, designed to improve language processing applications, enhance customer service, and support regionalized voice-based interactions.",
            "image": "https://www.4th-ir.com/favicon.ico",
        },
        "Land-Search": {
            "color": "alert alert-yellow",
            "description": "A specialized search tool that enables users to find land information quickly and accurately. This solution supports property seekers, real estate agents, and government entities in accessing reliable land data.",
            "image": "https://www.4th-ir.com/favicon.ico",
        },
    }

    for i in range(0, len(projects), 2):
        col1, col2 = st.columns(2)
        items = list(projects.items())[i : i + 2]

        # Add cards to columns
        if len(items) > 0:
            col1.markdown(
                create_project_card(items[0][0], items[0][1]), unsafe_allow_html=True
            )

        if len(items) > 1:
            col2.markdown(
                create_project_card(items[1][0], items[1][1]), unsafe_allow_html=True
            )


if __name__ == "__main__":
    main()
