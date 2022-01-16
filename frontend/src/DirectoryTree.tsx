import { MouseEvent } from "react";
import { Tree } from "@minoru/react-dnd-treeview";
import styles from "./DirectoryTree.module.css";
import { DirectoryRec } from "./types";
import { useAppSelector, useAppDispatch, selectDirectoryList, replaceDirectoryList } from "./store";
import { Emoji } from "emoji-mart";

interface TreeNode {
    id: number;
    text: string;
    parent: number;
    droppable: boolean;
    data: {
        icon_emoji: string;
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
        }
    }
}

function fromTree(tree: TreeNode): DirectoryRec {
    return {
        id: tree.id,
        title: tree.text,
        icon_emoji: tree.data.icon_emoji,
        parent_id: tree.parent,
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

export default function DirectoryTree() {
    const directoryList = useAppSelector(selectDirectoryList);
    const dispatch = useAppDispatch();

    function handleDrop(newTreeData: Array<TreeNode>) {
        newTreeData.forEach((tree: TreeNode) =>
            fetch(`http://localhost:5000/api/directories/${tree.id}`,
                {
                    headers: {
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    method: "POST",
                    body: JSON.stringify({
                        "title": tree.text,
                        "parent_id": tree.parent,
                        "icon_emoji": tree.data.icon_emoji,
                    })
                }
            )
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        window.alert(data.error.title + ": " + data.error.message);
                    } else {
                        dispatch(replaceDirectoryList(newTreeData.map(fromTree)));
                    }
                })
        );
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
        fetch("http://localhost:5000/api/directories",
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
                    dispatch(replaceDirectoryList([...directoryList, data.data]));
                }
            });
    }

    return (
        <div className={styles.DirectoryTree}>
            <Tree
                rootId={0}
                render={(node, { depth, isOpen, onToggle }) => (
                    <div className={styles.dir} style={{ marginLeft: depth * 10 }}>
                        {node.droppable && (
                            <div className={styles.icon} onClick={onToggle}>
                                {isOpen ? <DownArrow /> : <RightArrow />}
                            </div>
                        )}
                        {node?.data?.icon_emoji
                            ?
                            <Emoji emoji={node?.data?.icon_emoji!} size={24} />
                            : <img src="/blue-folder.png" alt="" />
                        }
                        <div className={styles.text}>
                            {node.text}
                        </div>
                    </div>
                )}
                tree={directoryList.map(asTree)}
                onDrop={handleDrop as any}
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
            />
            <button className={styles.button} onClick={handleAddToplevelDirectory}>
                Add Directory
            </button>
        </div>
    );
}