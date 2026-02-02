import asyncio
import logging
import config

logger = logging.getLogger(__name__)

class DownloadQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.workers = []
        self.processor_func = None

    async def start(self, processor_func):
        """
        Starts the worker tasks.
        processor_func: async function(task_data)
        """
        self.processor_func = processor_func
        for i in range(config.MAX_CONCURRENT_DOWNLOADS):
            worker = asyncio.create_task(self.worker(i))
            self.workers.append(worker)
        logger.info(f"Started {len(self.workers)} queue workers.")

    async def worker(self, worker_id):
        while True:
            # Get a "work item" out of the queue.
            task_data = await self.queue.get()
            
            client = task_data['client']
            message = task_data['message']
            url = task_data['url']
            status_msg = task_data['status_msg']

            try:
                logger.info(f"Worker {worker_id} starting task: {url}")
                # Update status to "Starting..."
                await status_msg.edit_text(f"🚀 **Starting Download...**\n`{url}`")
                
                # Execute the actual processing logic
                await self.processor_func(client, message, url, status_msg)
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                try:
                    await status_msg.edit_text(f"❌ **Queue Error**\n`{e}`")
                except:
                    pass
            finally:
                # Notify the queue that the item has been processed
                self.queue.task_done()

    async def add(self, client, message, url):
        """
        Adds a task to the queue and updates the user message.
        """
        # Send initial status message
        queue_pos = self.queue.qsize() + 1
        status_msg = await message.reply_text(f"zk **Added to Queue**\nPosition: {queue_pos}\n`{url}`")
        
        task_data = {
            'client': client,
            'message': message,
            'url': url,
            'status_msg': status_msg
        }
        
        await self.queue.put(task_data)
        return status_msg

# Global instance
queue_manager = DownloadQueue()
