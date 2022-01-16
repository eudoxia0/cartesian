import { configureStore, PayloadAction, createSlice } from '@reduxjs/toolkit';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux'
import { ClassRec, DirectoryRec } from "./types";

// Counter

interface CounterState {
    value: number
}

const initialCounterState: CounterState = {
    value: 0,
}

export const counterSlice = createSlice({
    name: 'counter',
    initialState: initialCounterState,
    reducers: {
        increment: (state) => {
            state.value += 1
        },
        decrement: (state) => {
            state.value -= 1
        },
        // Use the PayloadAction type to declare the contents of `action.payload`
        incrementByAmount: (state, action: PayloadAction<number>) => {
            state.value += action.payload
        },
    },
});

export const counterReducer = counterSlice.reducer;

export const { increment, decrement, incrementByAmount } = counterSlice.actions;

export const selectCount = (state: RootState) => state.counter.value;

// Directories

interface DirectoryListState {
    directories: Array<DirectoryRec>;
}

const initialDirectoryListState: DirectoryListState = {
    directories: [],
}

export const directoryListSlice = createSlice({
    name: 'directoryList',
    initialState: initialDirectoryListState,
    reducers: {
        addDirectory: (state: DirectoryListState, action: PayloadAction<DirectoryRec>) => {
            state.directories.push(action.payload);
        },
        replaceDirectoryList: (state: DirectoryListState, action: PayloadAction<Array<DirectoryRec>>) => {
            state.directories = action.payload;
        },
    },
});

export const directoryListReducer = directoryListSlice.reducer;

export const { addDirectory, replaceDirectoryList } = directoryListSlice.actions;

export const selectDirectoryList = (state: RootState) => state.directoryList.directories;

// Classes

interface ClassListState {
    classes: Array<ClassRec>;
}

const initialClassListState: ClassListState = {
    classes: [],
}

export const classListSlice = createSlice({
    name: 'classList',
    initialState: initialClassListState,
    reducers: {
        addClass: (state: ClassListState, action: PayloadAction<ClassRec>) => {
            state.classes.push(action.payload);
        },
        replaceClassList: (state: ClassListState, action: PayloadAction<Array<ClassRec>>) => {
            state.classes = action.payload;
        },
    },
});

export const classListReducer = classListSlice.reducer;

export const { addClass, replaceClassList } = classListSlice.actions;

export const selectClassList = (state: RootState) => state.classList.classes;

// Store

export const store = configureStore({
    reducer: {
        counter: counterReducer,
        directoryList: directoryListReducer,
        classList: classListReducer,
    },
});

// etc.

export type RootState = ReturnType<typeof store.getState>;

export type AppDispatch = typeof store.dispatch;

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
