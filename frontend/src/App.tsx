import { Routes, Route, Link } from "react-router-dom";
import Home from "./Home";
import FileList from "./FileList";
import styles from "./App.module.css";
import FileUploadPage from "./FileUploadPage";
import FileDetail from "./FileDetail";
import DirectoryTree from "./DirectoryTree";
import ClassList from "./ClassList";
import ClassDetail from "./ClassDetail";
import CreateObject from "./CreateObject";
import ObjectList from "./ObjectList";
import ObjectView from "./ObjectView";
import 'emoji-mart/css/emoji-mart.css';
import Settings from "./Settings";
import DirectoryContents from "./DirectoryContents";
import UncategorizedObjects from "./UncategorizedObjects";
import SearchPage from "./SearchPage";
import { dailyNoteTitle } from "./utils";

export default function App() {
  return (
    <div className={styles.App}>
      <div className={styles.leftPane}>
        <div className={styles.Logo}>
          <Link to="/">
            <img src="/static/coin.png" alt="Logo" />
          </Link>
        </div>
        <h1>Cartesian</h1>
        <nav>
          <ul>
            <li>
              <Link to={`/objects/Index`}>
                <img src="/static/home.png" alt="" />
                <span>Index</span>
              </Link>
            </li>
            <li>
              <Link to={`/objects/${dailyNoteTitle()}`}>
                <img src="/static/calendar-day.png" alt="" />
                <span>Daily Note</span>
              </Link>
            </li>
            <li>
              <Link to="/files">
                <img src="/static/files.png" alt="" />
                <span>Files</span>
              </Link>
            </li>
            <li>
              <Link to="/file-upload">
                <img src="/static/upload-file.png" alt="" />
                <span>Upload File</span>
              </Link>
            </li>
            <li>
              <Link to="/classes">
                <img src="/static/classes.png" alt="" />
                <span>Classes</span>
              </Link>
            </li>
            <li>
              <Link to="/create-object">
                <img src="/static/plus.png" alt="" />
                <span>Create Object</span>
              </Link>
            </li>
            <li>
              <Link to="/objects">
                <img src="/static/table.png" alt="" />
                <span>All Objects</span>
              </Link>
            </li>
            <li>
              <Link to="/search">
                <img src="/static/magnifier-left.png" alt="" />
                <span>Search</span>
              </Link>
            </li>
            <li>
              <Link to="/settings">
                <img src="/static/equalizer.png" alt="" />
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
    </div>
  );
}