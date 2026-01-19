        # Robustly find Datasets folder
        base_dir = os.path.dirname(os.path.abspath(__file__)) # backend/
        root_dir = os.path.dirname(base_dir) # project root
        dataset_dir = os.path.join(root_dir, "Datasets")
        
        if not os.path.exists(dataset_dir):
            print(f"⚠ Warning: Dataset directory not found at {dataset_dir}")
            return

        enrol_files = glob.glob(os.path.join(dataset_dir, "api_data_aadhar_enrolment", "*.csv"))
        demo_files = glob.glob(os.path.join(dataset_dir, "api_data_aadhar_demographic", "*.csv"))
        bio_files = glob.glob(os.path.join(dataset_dir, "api_data_aadhar_biometric", "*.csv"))