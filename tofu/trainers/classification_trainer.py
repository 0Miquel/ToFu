from tqdm import tqdm
from tofu.utils import *
from .base_trainer import BaseTrainer


class ClassificationTrainer(BaseTrainer):
    def __init__(self, config):
        super().__init__(config)

    def train_epoch(self, epoch):
        self.model.train()
        running_loss = 0
        # use tqdm to track progress
        with tqdm(self.train_dl, unit="batch") as tepoch:
            tepoch.set_description(f"Epoch {epoch + 1}/{self.n_epochs} train")
            # Iterate over data.
            for step, batch in enumerate(tepoch):
                batch = load_batch_to_device(batch, self.device)
                # zero the parameter gradients
                self.optimizer.zero_grad()
                # forward
                outputs = self.model(batch["imgs"])
                # loss
                loss = self.loss(outputs, batch["labels"])
                # backward
                loss.backward()
                self.optimizer.step()
                if self.scheduler is not None:
                    self.scheduler.step()
                # COMPUTE EPOCHS LOSS
                running_loss += loss.item()
                epoch_loss = running_loss / (step+1)
                # LEARNING RATE
                current_lr = self.optimizer.param_groups[0]['lr']
                tepoch.set_postfix({"loss": epoch_loss, "lr": current_lr})
        if self.logger is not None:
            self.logger.add({"loss": epoch_loss, "lr": current_lr}, "train")
        return epoch_loss

    def val_epoch(self, epoch):
        self.model.eval()
        stats = init_classification_metrics()
        with torch.no_grad():
            # use tqdm to track progress
            with tqdm(self.val_dl, unit="batch") as tepoch:
                tepoch.set_description(f"Epoch {epoch + 1}/{self.n_epochs} val")
                # Iterate over data.
                for step, batch in enumerate(tepoch):
                    batch = load_batch_to_device(batch, self.device)
                    # predict
                    outputs = self.model(batch["imgs"])
                    # loss
                    loss = self.loss(outputs, batch["labels"])
                    # compute metrics for this epoch and loss
                    stats = compute_classification_metrics(loss, outputs, batch["labels"], stats, step + 1)
                tepoch.set_postfix(**stats)
        if self.logger is not None:
            self.logger.add(metrics, "val")
        return stats["loss"]
