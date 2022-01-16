import styles from "./SimpleContainer.module.css";

interface Props {
    title: React.ReactNode,
    body: React.ReactNode,
}

export default function SimpleContainer<T>(props: Props) {
    return (
        <div className={styles.container}>
            <h1 className={styles.title}>
                {props.title}
            </h1>
            <div className={styles.body}>
                {props.body}
            </div>
        </div>
    );
}