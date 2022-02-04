import { MouseEvent } from "react";
import styles from "./Modal.module.css";

interface Props {
    title: string;
    body: React.ReactNode;
    visibility: boolean;
    onDecline: () => void;
    onAccept: () => void;
}

export default function Modal(props: Props) {
    function handleCancel(event: MouseEvent<HTMLButtonElement>) {
        event.preventDefault();
        props.onDecline();
    }

    function handleAccept(event: MouseEvent<HTMLButtonElement>) {
        event.preventDefault();
        props.onAccept();
    }

    return (
        <div className={styles.background + " " + (props.visibility ? styles.show : styles.hide)}>
            <div className={styles.container}>
                <div className={styles.box}>
                    <div className={styles.title}>
                        {props.title}
                    </div>
                    <div className={styles.body}>
                        {props.body}
                    </div>
                    <div className={styles.buttons}>
                        <button onClick={handleCancel}>
                            <img src="/static/cross.png" alt="" />
                            Cancel
                        </button>
                        <button onClick={handleAccept}>
                            <img src="/static/tick.png" alt="" />
                            Accept
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}