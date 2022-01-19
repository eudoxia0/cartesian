import { Routes, Route, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import Home from "./Home";
import FileList from "./FileList";
import styles from "./App.module.css";
import FileUploadPage from "./FileUploadPage";
import FileDetail from "./FileDetail";
import DirectoryTree from "./DirectoryTree";
import ClassList from "./ClassList";
import ClassDetail from "./ClassDetail";
import CreateObject from "./CreateObject";
import { useAppDispatch, replaceDirectoryList } from "./store";
import ObjectList from "./ObjectList";
import ObjectView from "./ObjectView";
import 'emoji-mart/css/emoji-mart.css';
import Settings from "./Settings";
import DirectoryContents from "./DirectoryContents";
import UncategorizedObjects from "./UncategorizedObjects";
import SearchPage from "./SearchPage";

const monthNames = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December"
];

function dailyNoteTitle(): string {
  const date = new Date();
  const [month, day, year] = [date.getMonth(), date.getDate(), date.getFullYear()];
  const monthName = monthNames[month];
  return `${monthName} ${day}, ${year}`;
}

export default function App() {
  const [loaded, setLoaded] = useState<boolean>(false);
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (!loaded) {
      fetch("http://localhost:5000/api/directories")
        .then(res => res.json())
        .then((data) => {
          setLoaded(true);
          dispatch(replaceDirectoryList(data.data));
        });
    }
  });
  return (
    <div className={styles.App}>
      <div className={styles.leftPane}>
        <div className={styles.Logo}>
          <Link to="/">
            <img src="/coin.png" alt="Logo" />
          </Link>
        </div>
        <h1>Cartesian</h1>
        <nav>
          <ul>
            <li>
              <Link to={`/objects/${dailyNoteTitle()}`}>
                <img src="/calendar-day.png" alt="" />
                <span>Daily Note</span>
              </Link>
            </li>
            <li>
              <Link to="/files">
                <img src="/files.png" alt="" />
                <span>Files</span>
              </Link>
            </li>
            <li>
              <Link to="/file-upload">
                <img src="/upload-file.png" alt="" />
                <span>Upload File</span>
              </Link>
            </li>
            <li>
              <Link to="/classes">
                <img src="/classes.png" alt="" />
                <span>Classes</span>
              </Link>
            </li>
            <li>
              <Link to="/create-object">
                <img src="/plus.png" alt="" />
                <span>Create Object</span>
              </Link>
            </li>
            <li>
              <Link to="/objects">
                <img src="/table.png" alt="" />
                <span>All Objects</span>
              </Link>
            </li>
            <li>
              <Link to="/search">
                <img src="/magnifier-left.png" alt="" />
                <span>Search</span>
              </Link>
            </li>
            <li>
              <Link to="/settings">
                <img src="/equalizer.png" alt="" />
                <span>Settings</span>
              </Link>
            </li>
          </ul>
        </nav>
        <DirectoryTree />
        <div className={styles.spacer}></div>
      </div>
      <div className={styles.rightPane}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/files/:fileId" element={<FileDetail />} />
          <Route path="/files" element={<FileList />} />
          <Route path="/file-upload" element={<FileUploadPage />} />
          <Route path="/classes/:classId" element={<ClassDetail />} />
          <Route path="/classes" element={<ClassList />} />
          <Route path="/create-object" element={<CreateObject defaultTitle="" />} />
          <Route path="/objects/:title" element={<ObjectView />} />
          <Route path="/objects" element={<ObjectList />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/directories/:dirId" element={<DirectoryContents />} />
          <Route path="/uncategorized" element={<UncategorizedObjects />} />
          <Route path="/search" element={<SearchPage />} />
        </Routes>
      </div>
    </div >
  );
}