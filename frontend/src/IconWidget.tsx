import { useEffect, useState } from "react";
import { Emoji, EmojiData, NimblePicker } from 'emoji-mart';
import data from 'emoji-mart/data/apple.json';
import styles from "./IconWidget.module.css";

interface Props {
    size: number;
    initialEmoji: string;
    onChange: (emojiId: string) => void;
}

function Placeholder(props: { size: number }) {
    const size = `${props.size}px`;
    return (
        <div className={styles.placeholder} style={{ width: size, height: size }}></div>
    )
}

export default function IconWidget(props: Props) {
    const [currentEmoji, setCurrentEmoji] = useState<string | null>(null);
    const [show, setShow] = useState<boolean>(false);

    useEffect(() => setCurrentEmoji((props.initialEmoji === "") ? null : props.initialEmoji), [props.initialEmoji]);

    function handleEmoji(emoji: EmojiData) {
        setCurrentEmoji(emoji.id || null);
        setShow(false);
        props.onChange(emoji.id || "");
    }

    return (
        <div className={styles.container}>
            <div onClick={() => setShow(!show)}>
                {currentEmoji ? <Emoji emoji={currentEmoji} size={props.size} native={true} /> : <Placeholder size={props.size} />}
            </div>
            <div className={show ? styles.show : styles.hide}>
                <div className={styles.picker}>
                    <NimblePicker data={data} native={true} onSelect={handleEmoji} />
                </div>
            </div>
        </div>
    );
}
