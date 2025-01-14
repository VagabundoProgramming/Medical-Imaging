# This file contains the classifier model
# It defines everything necessary to create the datasets, dataloader, 
# model, train, test and evaluation.

# To Create a new model change model_path to NULL
# To increase speed when training uncomment the .to(device) commands

import torch.nn as nn
from torch.utils.data import DataLoader
from load_data import *
from metrics import *

### GPU & Model & Initialize
#device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#print("Using device:", device)

# Give a path to a model file if we don't want to train another one.
# Change to None if we want to train the model
model_name = None

# If false it will skip training and training related data
do_training = True

# Define number of epochs
n_epochs = 70

### Load data and clean it up ###
data_path = "Data\\"
annotations, patch_data = open_data(data_path)
ids, ids_mod = get_ids(image_path="Data\\Annotated") 

# Clean Data
cleaned_patches = clean_patches(patch_data, ids_mod)

# Load Images
all_images = load_images(cleaned_patches) 

# Split Data
train_set, test_set = data_splitter(all_images, 5, 0)

# Define Datasets and Dataloaders
train_dataset = Cropped_Patches(train_set)
test_dataset  = Cropped_Patches(test_set)

train_loader = DataLoader(train_dataset, batch_size = 20, shuffle = True)
test_loader  = DataLoader(test_dataset, batch_size = 20, shuffle = False)

### Model
class M_model(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers_epic = nn.Sequential(
            nn.Conv2d(3, 6, 5, 2, 2),
            nn.MaxPool2d(2,2),
            nn.ReLU(),

            nn.Conv2d(6, 12, 3, 2, 1),
            nn.MaxPool2d(2,2),
            nn.ReLU(),

            nn.Conv2d(12, 6, 5, 2, 2),
            nn.MaxPool2d(2,2),
            nn.ReLU(),

            nn.Conv2d(6, 1, 3, 1, 1),
            nn.ReLU(),

            nn.Flatten(),
            nn.Linear(16,2),
            nn.ReLU()
        )

    def forward(self, x):
        x = self.layers_epic(x)
        return x

# Initialize model
def start_model(model_name = None):
    if not model_name:
        model = M_model()#.to(device)
    else:
        model = torch.load(f"Models/{model_name}")#.to(device)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters())
    return model, loss_fn, optimizer

model, loss_fn, optimizer = start_model(model_name = model_name) 

### Define Train and Test
def train(dataloader, model, loss_fn, optimizer, threshold = 0.5):
    size = len(dataloader.dataset)
    
    model.train()
    for batch, (X, y) in enumerate(dataloader):
        #X, y = X.to(device), y.to(device)
        
        pred = model(X)
        loss = loss_fn(pred, y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step() 

        if batch % 10 == 0: 
            loss, current = loss.item(), batch * len(X)
            print(f"loss: {loss:>7f} [{current:>5d}/{size:>5d}]")
        
def test (dataloader, model, loss_fn):
    size = len(dataloader.dataset)
    num_batches = len(dataloader)

    model.eval()
    test_loss, correct = 0,0
    with torch.no_grad():
        for X, y in dataloader:
            #X, y = X.to(device), y.to(device)

            pred = model(X)
            test_loss += loss_fn(pred, y).item()
           
            for p, sub_y in zip(pred, y):
                
                if p[0] < p[1]:   # (0,1) == infected
                    sub_p = True
                else:
                    sub_p = False
                
                if sub_y[0] < sub_y[1]:   # (0,1) == infected
                    sub_y = True
                else:
                    sub_y = False
                
                if sub_p == sub_y:
                    correct += 1

    test_loss /= num_batches
    correct /=size
    print(f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>0.8f} \n")
    return test_loss, correct

### Train loop
def train_loop(n_epochs, model, loss, optimizer):
    loss_l = []
    acc_l = []

    # Do n epochs
    for ep in range(n_epochs):
        print(f"Epoch {ep+1}: \n")
        train(train_loader, model, loss, optimizer)
        holder = test(test_loader, model, loss)
        loss_l.append(holder[0])
        acc_l.append(holder[1])

        # Save the model each 5 epochs
        if (ep + 1) % 5 == 0:
            torch.save(model, f"Models/Classifier_Model_parameters_{ep+1}.pt")

    print("Finish training")
    return loss_l, acc_l

if do_training:
    loss, acc = train_loop(n_epochs, model, loss_fn, optimizer)


### Display Loss
if do_training:
    display_loss_acc(loss, acc, "Classifier_Model")

### Display Confusion Matrix
#display_conf_m(test_loader, model, "Classifier_Model")

### Average acc
acc_l, avg_acc, std_acc = average_accuracy(model, loss_fn, test, all_images, 5, model_name)
print(f"The model {model_name}")
print(f"With the accuracities:\n {acc_l}\n")
print(f"Has an average accuracy of: {avg_acc}")
print(f"And a standard deviation of: {std_acc}")
