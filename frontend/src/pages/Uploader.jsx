import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import styles from "../components/Uploader.module.css";

export default function Uploader () {
    const [files, setFiles] = useState([]);
    const [oldFiles, setOldFiles] = useState([]);
    const navigate = useNavigate();

    // Run when the first component loads
    useEffect(() => {
        api.get("/api/dashboard/files/")
          .then(res => setOldFiles(res.data))
          .catch(err => console.log(err));
    }, [] ) //<- This '[]' tells React to only run this once

    const handleFile = async (e) => {
        e.preventDefault();

        const formData = new FormData();

        for (let i = 0; i < files.length; i++)
        {
            formData.append("file", files[i])
        }

        try
        {
            // Submit file to django'
            const res = await api.post("/api/dashboard/fileUpload/", formData);

            navigate(`/runner/${res.data.file_id[0]}`);
        }
        catch (error) {
    console.log("Status:", error.response?.status);
    console.log("Data:", error.response?.data);
}
    }

    return (
    <div className={styles.mainLayout}>
      <div className={styles.sidebar}>
        <div>
        </div>

        <div>
          <h2>Files Uploaded</h2>

          {oldFiles.length === 0 ? (
            <p>No uploaded files yet.</p>
          ) : (
            oldFiles.map((file) => (
              <button
                key={file.id}
                type="button"
                onClick={() => navigate(`/runner/${file.id}`)}
              >
                {file.name}
              </button>
            ))
          )}
        </div>

        <div>
          <h1 className={styles["viga-regular"]}>CRUXERRA</h1>
          <p>Easily upload your csv file and calculate your race times.</p>
        </div>
      </div>

      <div className={styles.main}>
        <div className={styles["upload-card"]}>
          <h2>Race Data Dashboard</h2>

          <hr />

          <h5>Upload Race CSV files</h5>

          <form onSubmit={handleFile}>
            <div className={styles.fileRow}>
              <label className={styles.uploadButton}>
                Choose CSV Files
                <input
                  name="file"
                  type="file"
                  multiple
                  accept=".csv"
                  onChange={(e) => setFiles(Array.from(e.target.files))} // Create array of files
                  className={styles.fileInput}
                />
              </label>
              <p>
                {files.length > 0
                  ? `${files.length} file(s) selected`
                  : "No files selected"}
              </p>
            </div>

            <button className={`btn ${styles["btn-gradient"]}`} type="submit">
              Submit CSV File(s)
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
