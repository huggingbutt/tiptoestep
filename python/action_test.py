import mmap
from tiptoestep.proto import Message, MessageSerializer

if __name__ == '__main__':
    filename = "/Users/admin/.cache/tiptoestep/0_1.mmf"
    file = open(filename, "r+b")
    mm = mmap.mmap(file.fileno(), 1024 * 16)
    data = mm[:266]

    msg = MessageSerializer.deserialize(data)
    print(msg.observation)
    mm.close()
    file.close()


