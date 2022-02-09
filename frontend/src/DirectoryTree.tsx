import { MouseEvent, useEffect, useState } from "react";
import { Tree } from "@minoru/react-dnd-treeview";
import styles from "./DirectoryTree.module.css";
import { DirectoryRec } from "./types";
import { Emoji } from "emoji-mart";
import Modal from "./Modal";
import IconWidget from "./IconWidget";
import { Link } from "react-router-dom";

interface TreeNode {
    id: number;
    text: string;
    parent: number;
    droppable: boolean;
    data: {
        icon_emoji: string;
        cover_id: number | null;
        created_at: number;
    }
}

const ROOT_ID: number = 0;

function asTree(dir: DirectoryRec): TreeNode {
    return {
        id: dir.id,
        text: dir.title,
        parent: dir.parent_id ? dir.parent_id : ROOT_ID,
        droppable: true,
        data: {
            icon_emoji: dir.icon_emoji,
            cover_id: dir.cover_id,
            created_at: dir.created_at,
        }
    }
}

function fromTree(tree: TreeNode): DirectoryRec {
    return {
        id: tree.id,
        title: tree.text,
        icon_emoji: tree.data.icon_emoji,
        cover_id: tree.data.cover_id,
        parent_id: (tree.parent === ROOT_ID) ? null : tree.parent,
        created_at: tree.data.created_at,
    }
}

function CustomPlaceholder(props: any) {
    return <li><hr /></li>;
}

function RightArrow() {
    return (
        <div className={styles.arrow}>
            ⯈
        </div>
    );
}

function DownArrow() {
    return (
        <div className={styles.arrow}>
            ⯆
        </div>
    );
}

function TreeNodeComponent(props: { node: TreeNode; depth: number; isOpen: boolean; handleEditDirectory: (dir: DirectoryRec) => void; onToggle: () => void; }) {
    const node = props.node;

    return (
        <div className={styles.dir} style={{ marginLeft: props.depth * 10 }}>
            {node.droppable && (
                <div className={styles.icon} onClick={props.onToggle}>
                    {props.isOpen ? <DownArrow /> : <RightArrow />}
                </div>
            )}
            {node?.data?.icon_emoji
                ?
                <Emoji emoji={node?.data?.icon_emoji!} size={24} native={true} />
                : <img src="/static/blue-folder.png" alt="" />
            }
            <div className={styles.text}>
                <Link to={`/directories/${node.id}`}>
                    {node.text}
                </Link>
            </div>
            <div className={styles.spacer}></div>
            <img
                className={styles.edit}
                src="/static/pencil.png"
                alt=""
                onClick={_ => props.handleEditDirectory(fromTree(node as TreeNode))}
            />
        </div>
    );
}

function TreeWrapper(props: { directoryList: Array<DirectoryRec>; handleEditDirectory: (dir: DirectoryRec) => void; handleDrop: any }) {
    return (
        <Tree
            rootId={0}
            render={(node, { depth, isOpen, onToggle }) => (
                <TreeNodeComponent
                    node={node as TreeNode}
                    depth={depth}
                    isOpen={isOpen}
                    handleEditDirectory={props.handleEditDirectory}
                    onToggle={onToggle} />
            )}
            tree={props.directoryList.map(asTree)}
            onDrop={props.handleDrop}
            classes={{
                placeholder: styles.placeholder,
            }}
            sort={false}
            insertDroppableFirst={false}
            canDrop={(tree, { dragSource, dropTargetId }) => {
                if (dragSource?.parent === dropTargetId) {
                    return true;
                }
            }}
            dropTargetOffset={5}
            placeholderRender={(node, { depth }) => (
                <CustomPlaceholder node={node} depth={depth} />
            )}
            initialOpen={true}
        />
    );
}

interface State {
    loaded: boolean;
    directories: Array<DirectoryRec>;
}

export default function DirectoryTree() {
    const [showEdit, setShowEdit] = useState<boolean>(false);
    const [editDir, setEditDir] = useState<DirectoryRec | null>(null);
    const [editEmoji, setEditEmoji] = useState<string>("");
    const [editTitle, setEditTitle] = useState<string>("");

    const [directoryList, setDirectoryList] = useState<State>({ loaded: false, directories: [] });

    useEffect(() => {
        if (!directoryList.loaded) {
            fetch("/api/directories")
                .then(res => res.json())
                .then((data) => setDirectoryList({ loaded: true, directories: data.data }));
        }
    });

    function handleDrop(newTreeData: Array<TreeNode>) {
        newTreeData.forEach((tree: TreeNode) => {
            const dir: DirectoryRec = fromTree(tree);
            fetch(`/api/directories/${tree.id}`,
                {
                    headers: {
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    method: "POST",
                    body: JSON.stringify({
                        "title": dir.title,
                        "parent_id": dir.parent_id,
                        "icon_emoji": dir.icon_emoji,
                    })
                }
            )
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        window.alert(data.error.title + ": " + data.error.message);
                    } else {
                        setDirectoryList({
                            loaded: directoryList.loaded,
                            directories: newTreeData.map(fromTree),
                        });
                    }
                })
        });
    }

    function handleAddToplevelDirectory(event: MouseEvent<HTMLButtonElement>) {
        event.preventDefault();
        let title = prompt("Title");
        if (!title) {
            return;
        }
        title = title.trim();
        if (title.length === 0) {
            window.alert("Directory titles can't be empty.");
            return;
        }
        fetch("/api/directories",
            {
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                method: "POST",
                body: JSON.stringify({
                    "title": title,
                    "parent_id": null,
                    "icon_emoji": "",
                })
            }
        )
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    window.alert(data.error.title + ": " + data.error.message);
                } else {
                    setDirectoryList({
                        loaded: directoryList.loaded,
                        directories: [...directoryList.directories, data.data],
                    });
                }
            });
    }

    function handleEditDirectory(dir: DirectoryRec) {
        setEditDir(dir);
        setEditTitle(dir.title);
        setEditEmoji(dir.icon_emoji);
        setShowEdit(true);
    }

    function handleSaveDirectoryChanges() {
        setShowEdit(false);
        const dir = editDir!;
        const newTitle = editTitle;
        const newEmoji = editEmoji;
        setEditDir(null);
        setEditTitle("");
        setEditEmoji("");
        fetch(`/api/directories/${dir.id}`,
            {
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                method: "POST",
                body: JSON.stringify({
                    "title": newTitle,
                    "parent_id": dir.parent_id,
                    "icon_emoji": newEmoji,
                })
            }
        )
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    window.alert(data.error.title + ": " + data.error.message);
                } else {
                    const existing = directoryList.directories.filter((d: DirectoryRec) => (d.id !== dir.id));
                    setDirectoryList({
                        loaded: directoryList.loaded,
                        directories: [
                            ...existing,
                            data.data
                        ],
                    });
                }
            });
    }

    function handleDeleteDirectory(dirId: number) {
        setShowEdit(false);
        const dir = editDir!;
        setEditDir(null);
        setEditTitle("");
        setEditEmoji("");
        fetch(`/api/directories/${dir.id}`,
            {
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                method: "DELETE",
            }
        )
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    window.alert(data.error.title + ": " + data.error.message);
                } else {
                    const existing = directoryList.directories.filter((d: DirectoryRec) => (d.id !== dir.id));
                    setDirectoryList({
                        loaded: directoryList.loaded,
                        directories: [
                            ...existing,
                        ],
                    });
                }
            });
    }

    return (
        <div className={styles.DirectoryTree}>
            {directoryList.directories.length > 0 ?
                <TreeWrapper directoryList={directoryList.directories} handleDrop={handleDrop as any} handleEditDirectory={handleEditDirectory} />
                :
                <span></span>
            }
            <div className={styles.dir} style={{ marginLeft: 20, marginTop: 20 }}>
                <img src="/static/blue-folder.png" alt="" />
                <div className={styles.text}>
                    <Link to={`/uncategorized`}>
                        Uncategorized
                    </Link>
                </div>
            </div>
            <button className={styles.button} onClick={handleAddToplevelDirectory}>
                Add Directory
            </button>
            <Modal
                title="Edit Directory"
                visibility={showEdit}
                body={editDir &&
                    <div>
                        Icon: <IconWidget size={64} initialEmoji={editEmoji} onChange={e => setEditEmoji(e)} />
                        Title:
                        <input type="text" value={editTitle} onChange={e => setEditTitle(e.target.value)} />
                        <button onClick={_ => handleDeleteDirectory(editDir.id)}>
                            Delete
                        </button>
                    </div>
                }
                onDecline={() => setShowEdit(false)}
                onAccept={handleSaveDirectoryChanges}
            />
        </div>
    );
}