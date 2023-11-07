
from src.models.model import MuMRVQ
from pytorch_lightning.cli import LightningCLI
from src.dataloading.datasets import CustomAudioDataModule
from pytorch_lightning.cli import SaveConfigCallback
from pytorch_lightning import LightningDataModule, LightningModule, Trainer
from pytorch_lightning.loggers import WandbLogger
from pytorch_lightning.callbacks import ModelCheckpoint
import yaml
import os
import shutil

class LoggerSaveConfigCallback(SaveConfigCallback):
    def save_config(self, trainer: Trainer, pl_module: LightningModule, stage: str) -> None:
            if trainer.logger is not None:
                config = self.parser.dump(self.config, skip_none=False)  # Required for proper reproducibility
                with open(self.config_filename, "r") as config_file:
                    config = yaml.load(config_file, Loader=yaml.FullLoader)
                    trainer.logger.experiment.config.update(config)
        

class MyLightningCLI(LightningCLI):
    def add_arguments_to_parser(self, parser):
        parser.link_arguments("model.encoder.init_args.n_codebooks", "model.decoder.init_args.n_codebooks")
        parser.link_arguments("model.encoder.init_args.emebdding_size", "model.decoder.init_args.eùbedding_size")
        parser.link_arguments("model.encoder.init_args.card", "model.decoder.init_args.card")
        parser.link_arguments("model.encoder.init_args.embedding_behaviour", "model.decoder.init_args.embedding_behaviour")
        parser.link_arguments("model.encoder.init_args.sequence_len", "model.decoder.init_args.sequence_len")
        parser.link_arguments("data.target_sample_rate","model.encodec.init_args.sample_rate")
        parser.add_argument("--log", default=False)
        parser.add_argument("--log_model", default=True)
        parser.add_argument("--ckpt_path", default="MuMRVQ_checkpoints")

if __name__ == "__main__":
    
    cli = MyLightningCLI(model_class=MuMRVQ, datamodule_class=CustomAudioDataModule, seed_everything_default = 123, run = False, save_config_callback=LoggerSaveConfigCallback, save_config_kwargs={"overwrite":True})
    
    
    cli.instantiate_classes()

    
    if cli.config.log:
        logger = WandbLogger(project="MuMRVQ")
    else:
        logger = None
        
        
    
    cli.trainer.logger = logger
    
    experiment_name = cli.trainer.logger.experiment.name
    ckpt_path = cli.config.ckpt_path
    if not os.path.exists(os.path.join(ckpt_path,experiment_name)):
        os.makedirs(os.path.join(cli.config.ckpt_path,experiment_name))
    shutil.copy(cli.config.config[0],os.path.join(cli.config.ckpt_path,experiment_name))
    if cli.config.log_model:
        callbacks = [ModelCheckpoint(os.path.join(cli.config.ckpt_path,experiment_name),monitor="val_crossentropy_simple",save_top_k=1)]
        cli.trainer.callbacks = cli.trainer.callbacks + callbacks
        
    
        
        
    
        
    
    cli.trainer.fit(model=cli.model,datamodule=cli.datamodule)
