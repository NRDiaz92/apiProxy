#!/bin/bash

gunicorn -b $FLASK_IP:$FLASK_PORT $FLASK_APP:app -w $FLASK_WORKERS --threads $FLASK_THREADS