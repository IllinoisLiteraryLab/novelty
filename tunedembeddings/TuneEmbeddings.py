# Tune Embeddings

# This script uses Sentence Transformers to fine-tune  
# a pre-trained model on training pairs from lit studies.

# This version June 2024.
import logging, argparse
import torch, os
import pandas as pd

from datasets import Dataset
from sentence_transformers import (
    SentenceTransformer,
    SentenceTransformerTrainer,
    SentenceTransformerTrainingArguments
)
from sentence_transformers import losses
from sentence_transformers.training_args import BatchSamplers
from sentence_transformers.evaluation import BinaryClassificationEvaluator

import numpy as np

print("Currently active directory:", os.getcwd())

# Configure logging
class FlushingHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

# Setup logging to use the flushing handler
logging.basicConfig(level=logging.INFO, handlers=[FlushingHandler()])
logger = logging.getLogger(__name__)

logger.info("This log is flushed immediately.")

# Command line arguments include
# -d    datasource  the path to the training data, a TSV file with columns 'anchor' and 'positive'
# -o    outputdir   the path to the output directory

# Parse command line arguments
parser = argparse.ArgumentParser(description='Tune Embeddings')
parser.add_argument('-d', '--datasource', type=str, help='Path to the training data (TSV file with columns "anchor" and "positive")')
parser.add_argument('-o', '--outputdir', type=str, help='Path to the output directory')
args = parser.parse_args()

# Get the values of the command line arguments
datasource = args.datasource
outputdir = args.outputdir

# 1. load a model to finetune

model = SentenceTransformer('all-distilroberta-v1')
# guide = SentenceTransformer('all-distilroberta-v1')

# Check for CUDA availability
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("Using CUDA:", torch.cuda.get_device_name(0))
else:
    # Fallback to MPS if CUDA is not available and you are on an Apple Silicon Mac
    device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
    print("Using:", device)

# Send models to the selected device
model.to(device)
# guide.to(device)

print(f'Device: {device}')

# 2. load data for training

# datasource is now specified as a command line argument
# previously:
# datasource = 'final_pairs.tsv' (leaving these lines here for reference)
# datasource = 'novelty/tunedembeddings/all_synthetic_training_pairs.tsv'

raw_data = pd.read_csv(datasource, sep='\t')

# shuffle raw_data and then divide it into a test dataset of 2000 pairs
# and a training dataset that has everything else
raw_data = raw_data.sample(frac=1).reset_index(drop=True)
eval_data = raw_data.loc[0:2199, :]
train_data = raw_data.loc[2200:, :]

# Enlarge the eval data to contain 11000 false alignments after the 2000 correct ones
anchor_extended = eval_data['anchor'].tolist() * 6
positive_extended = eval_data['positive'].tolist() + list(np.roll(eval_data['positive'].tolist(), 1)) + \
	list(np.roll(eval_data['positive'].tolist(), 2)) + list(np.roll(eval_data['positive'].tolist(), 3)) + \
	list(np.roll(eval_data['positive'].tolist(), 4)) + list(np.roll(eval_data['positive'].tolist(), 5))
score = [1] * 2200 + [0] * 11000
eval_data = pd.DataFrame({'anchor': anchor_extended, 'positive': positive_extended, 'score': score})

train_dataset = Dataset.from_pandas(train_data.loc[ :, ['anchor', 'positive']])
eval_dataset = Dataset.from_pandas(eval_data)

# 3. define a loss function
# loss = losses.CachedGISTEmbedLoss(model, guide, mini_batch_size=16)
loss = losses.MultipleNegativesRankingLoss(model)

# 4. define a function to compute the evaluation metrics

binary_acc_evaluator = BinaryClassificationEvaluator(
    sentences1=eval_dataset["anchor"],
    sentences2=eval_dataset["positive"],
    labels=eval_dataset["score"],
    name="binary-evaluator",
)

# 5. (Optional) Specify training arguments
final_dir = outputdir + '/final'

args = SentenceTransformerTrainingArguments(
    # Required parameter:
    output_dir= outputdir,
    # Optional training parameters:
    num_train_epochs=9,
    per_device_train_batch_size=80,
    per_device_eval_batch_size=80,
    warmup_ratio=0.1,
    fp16 = True,  # Set to False if you get an error that your GPU can't run on FP16
    bf16= False,  # Set to True if you have a GPU that supports BF16
	evaluation_strategy= "epoch",
    save_strategy= "epoch",
    batch_sampler=BatchSamplers.NO_DUPLICATES,  # MultipleNegativesRankingLoss benefits from no duplicate samples in a batch
)
print('Preparing to evaluate.', flush = True)

# 6. Evaluate the base model
binary_acc_evaluator(model)

# 7. Create a trainer & train
trainer = SentenceTransformerTrainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    loss=loss,
    evaluator=binary_acc_evaluator,
)
trainer.train()

# 8. Save the model

model.save_pretrained(final_dir)

#9. A final evaluation
binary_acc_evaluator(model)
print('Done.')
