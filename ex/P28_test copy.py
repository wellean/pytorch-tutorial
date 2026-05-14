    

import torch


outputs = torch.tensor([[0.1, 0.2],
                        [0.3, 0.4]])
print(outputs.argmax(dim=1))

preds = outputs.argmax(dim=1)
labels = torch.tensor([0, 1])
print(preds == labels)
print((preds == labels).sum().item())