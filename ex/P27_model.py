import torch.nn as nn
# 搭建神经网络
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.model = nn.Sequential(
            nn.Conv2d(in_channels=3, out_channels=32, kernel_size=5, stride=1, padding=2),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(in_channels=32, out_channels=32, kernel_size=5, stride=1, padding=2),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=5, stride=1, padding=2),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Flatten(),
            nn.Linear(1024, 64),
            nn.Linear(64, 10)
        )

    def forward(self, x):
        x = self.model(x)
        return x
    
import torch


# 测试网络结构是否正确
if __name__ == "__main__":  # main函数，此行代码实际上是 main() 的原始写法，Python 解释器会将其转换为 main() 函数的调用，然后程序从 main() 函数开始执行。
    net = Net()
    input = torch.ones(64, 3, 32, 32)
    output = net(input)
    print(output.shape)
