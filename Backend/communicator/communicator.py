import mmap
import asyncio

# states
# 0 - unreadable
# 1 - python write
# 2 - c# write

class Communicator:
    def __init__(self):
        self.maps: dict[str, mmap.mmap] = {}

    def create(self, size, tag):
        tmap = mmap.mmap(-1, size, tagname=f"Exoplanets\\{tag}", access=mmap.ACCESS_DEFAULT)
        self.maps.update({tag: tmap})

    def write(self, tag, data, pos):
        tmap = self.maps[tag]
        tmap.seek(pos)
        tmap.write(data)
        tmap.seek(0)
        tmap.write_byte(1)

    async def read(self, tag):
        tmap = self.maps[tag]
        while True:
            tmap.seek(0)
            if tmap.read_byte() == 2:
                break
            await asyncio.sleep(0.01)
        tmap.seek(1)
        return tmap.read(tmap.size() - 1)
    
    def close(self, tag):
        self.maps[tag].close()
        del self.maps[tag]
    

async def main():
    communicator = Communicator()
    communicator.create(1024, "test")
    communicator.write("test", "Hello from python".encode())
    print(await communicator.read("test"))
    communicator.close("test")

if __name__ == "__main__":
    asyncio.run(main())
