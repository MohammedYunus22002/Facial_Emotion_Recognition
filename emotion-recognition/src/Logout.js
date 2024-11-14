import React from "react";
import { useNavigate } from "react-router-dom";

function Logout() {
  const navigate = useNavigate();

  const handleLogout = async () => {
    // Remove the token from localStorage
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    // Optionally, you can make a request to the backend to invalidate the session (if implemented)
    // await axios.post("http://localhost:8000/logout");

    // Navigate to the login page
    navigate("/login");
  };

  return (
    <div style={styles.container}>
      <button onClick={handleLogout} style={styles.button}>Logout</button>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    justifyContent: "center",
  },
  button: {
    padding: "0.8rem",
    fontSize: "1rem",
    color: "#fff",
    backgroundColor: "#007bff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
  },
};

export default Logout;
