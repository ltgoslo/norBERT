#! /bin/env python3
#! coding: utf-8

import sys
import pandas as pd
import torch
from torch.utils import data
from transformers import AdamW
from transformers import BertForSequenceClassification, AutoTokenizer


def multi_acc(y_pred, y_test):
    batch_predictions = torch.log_softmax(y_pred, dim=1).argmax(dim=1)
    correctness = batch_predictions == y_test
    acc = torch.sum(correctness).item() / y_test.size(0)
    return acc


EPOCHS = 10

modelname = sys.argv[1]
dataset = sys.argv[2]

tokenizer = AutoTokenizer.from_pretrained(modelname)
model = BertForSequenceClassification.from_pretrained(modelname)
model.train()

optimizer = AdamW(model.parameters(), lr=1e-5)

print("Reading train data...")
train_data = pd.read_csv(dataset)
train_data.columns = ["labels", "text"]
print("Train data reading complete.")

texts = train_data.text.to_list()
text_labels = train_data.labels.to_list()

# for param in model.base_model.parameters():
#    param.requires_grad = False

labels = torch.tensor(text_labels)
print("Tokenizing..")
encoding = tokenizer(texts, return_tensors='pt', padding=True, truncation=True,
                     max_length=256)
input_ids = encoding['input_ids']
attention_mask = encoding['attention_mask']
print("Tokenizing finished.")

train_dataset = data.TensorDataset(input_ids, attention_mask, labels)
train_iter = data.DataLoader(train_dataset, batch_size=16, shuffle=True)

for epoch in range(EPOCHS):
    losses = 0
    total_train_acc = 0
    for i, (text, mask, label) in enumerate(train_iter):
        optimizer.zero_grad()
        outputs = model(text, attention_mask=mask, labels=label)
        loss = outputs.loss
        losses += loss.item()
        predictions = outputs.logits
        accuracy = multi_acc(predictions, label)
        total_train_acc += accuracy
        loss.backward()
        optimizer.step()
    train_acc = total_train_acc / len(train_iter)
    train_loss = losses / len(train_iter)
    print(f"Epoch: {epoch}, Loss: {train_loss:.4f}, Accuracy: {train_acc:.4f}")

# model.eval()
#
# sentences = ["Polanski er den snikende uhygges mester", "Utvalget diktere er skjevt ."]
#
# for s in sentences:
#     print(s)
#     encoding = tokenizer([s], return_tensors='pt', padding=True, truncation=True,
#                          max_length=256)
#     input_ids = encoding['input_ids']
#     print(tokenizer.convert_ids_to_tokens(input_ids[0]))
#     attention_mask = encoding['attention_mask']
#     outputs = model(input_ids, attention_mask=attention_mask)
#     print(outputs)
