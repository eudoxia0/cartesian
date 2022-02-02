#!/usr/bin/env bash

cd frontend
npm run build
cd ..
rm -rf server/theatre/static
mkdir server/theatre/static
cp -a frontend/build/. server/theatre/static