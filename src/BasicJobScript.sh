#!/usr/local_rwth/bin/zsh


### Job name
#SBATCH --job-name=FredericMasterThesisGAN

### Output path for stdout and stderr
### %J is the job ID, %I is the array ID
#SBATCH --output=output_%J.txt

### Request the time you need for execution. The full format is D-HH:MM:SS
### You must at least specify minutes OR days and hours and may add or
### leave out any other parameters
#SBATCH --time=3-00:00:00

### Request the amount of memory you need for your job.
### You can specify this in either MB (1024M) or GB (4G).
#SBATCH --mem-per-cpu=32G

### Request a host with a Volta GPU
### If you need two GPUs, change the number accordingly
#SBATCH --gres=gpu:volta:1

### if needed: switch to your working directory (where you saved your program)
#cd $HOME/Master-Thesis_GAN-level-gen/src/

### Load modules
module load python/3.8.7
module load cuda/11.4
module load cudnn/8.4.0

pip3 install --user -r requirements.txt

### Make sure you have 'tensorflow-gpu' installed, because using
### 'tensorflow' will lead to your program not using the requested
### GPU.
python3 -c "import tensorflow as tf; print(tf.__version__)"
python3 -c "import tensorflow as tf; print('Num GPUs Available: ', len(tf.config.list_physical_devices('GPU')))"


### Execute your application
python3 trainer/TrainNeuralNetwork.py


### TO RUN sbatch < BasicJobScript.sh
### TO View in QUEUE squeue -u $USER