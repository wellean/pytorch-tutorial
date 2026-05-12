import torch
import torchvision
import os

vgg16 = torchvision.models.vgg16(pretrained=False)
# 保存方式1：保存整个模型
os.makedirs("models", exist_ok=True)    # 确保保存目录存在，若目录不存在则创建，若目录已存在则不会有任何影响
torch.save(vgg16, "models/vgg16.pth")

# 保存方式2：只保存模型的状态字典（推荐）
torch.save(vgg16.state_dict(), "models/vgg16_state_dict.pth")

# 自建模型示例
class Mymodel(torch.nn.Module):
    def __init__(self):
        super(Mymodel, self).__init__()
        self.conv1 = torch.nn.Conv2d(3, 16, kernel_size=3, padding=1)
        self.conv2 = torch.nn.Conv2d(16, 32, kernel_size=3, padding=1)

    def forward(self, x):
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        return x

mymodel = Mymodel()

torch.save(mymodel, "models/mymodel.pth")