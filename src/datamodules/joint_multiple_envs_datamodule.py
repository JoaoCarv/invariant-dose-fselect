from torch.utils.data import Dataset, DataLoader, Subset, ConcatDataset
from pytorch_lightning import LightningDataModule
from torchvision import transforms as transform_lib
import torchvision.transforms.functional as F
from torch.nn.functional import interpolate

from torchvision import transforms, datasets
from src.datamodules.components.single_envs import SingleEnv,SingleEnvCV


class PL_JointMultipleEnvs(LightningDataModule):

    def __init__(self, data_dir,
                 batch_size,
                 num_workers,
                 resize,
                 pin_memory,
                 extract_roi,
                 masked,
                 train_env_1,
                 train_env_2,
                 test_env,
                 val_split=0.1,
                 test_split=0.1
                 ):

        super().__init__()
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.data_dir = data_dir
        self.pin_memory = pin_memory

        self.val_split = val_split
        self.test_split = test_split

        self.extract_roi = extract_roi
        self.resize = resize
        self.masked = masked

        self.train_env_1 = train_env_1
        self.train_env_2 = train_env_2
        self.test_env = test_env




    def prepare_data(self):
        pass

    def setup(self, stage=None):

        self.transform_train = None
        self.transform_val = None
        # called on every GPU
        if stage == "fit" or stage is None:
            train_env_ds_1 = SingleEnv(root_dir=self.data_dir,
                                     env=self.train_env_1,
                                     resize=self.resize,
                                     extract_roi=self.extract_roi,
                                     masked=self.masked)
            
            n_val_1 = int(len(train_env_ds_1)*self.val_split)
            n_test_1 = int(len(train_env_ds_1)*self.test_split)
            idx_train_1 = list(range(len(train_env_ds_1)))
            idx_val_1 = list(range(len(train_env_ds_1)))
            

            train_ds_1 = Subset(train_env_ds_1, idx_train_1[n_val_1:-n_test_1])
            val_ds_1 = Subset(train_env_ds_1, idx_val_1[:n_val_1])

            train_env_ds_2 = SingleEnv(root_dir=self.data_dir,
                                       env=self.train_env_2,
                                       resize=self.resize,
                                       extract_roi=self.extract_roi,
                                       masked=self.masked)

            n_val_2 = int(len(train_env_ds_2) * self.val_split)
            n_test_2 = int(len(train_env_ds_2) * self.test_split)
            idx_train_2 = list(range(len(train_env_ds_2)))
            idx_val_2 = list(range(len(train_env_ds_2)))

            train_ds_2 = Subset(train_env_ds_2, idx_train_2[n_val_2:-n_test_2])
            val_ds_2 = Subset(train_env_ds_2, idx_val_2[:n_val_2])

            train_ds = ConcatDataset([train_ds_1,train_ds_2])
            val_ds = ConcatDataset([val_ds_1, val_ds_2])


            self.train_ds = DataSubSet(train_ds, transform=self.transform_val)
            self.val_ds = DataSubSet(val_ds, transform=self.transform_val)

        if stage  == "test" or stage is None:
            test_env_ds = SingleEnv(root_dir=self.data_dir,
                                     env=self.test_env,
                                     resize=self.resize,
                                     extract_roi=self.extract_roi,
                                     masked=self.masked)

            n_test = int(len(test_env_ds)*self.test_split)
            idx_test = list(range(len(test_env_ds)))

            test_ds = Subset(test_env_ds,idx_test[-n_test:])
            self.test_ds = DataSubSet(test_ds,transform=self.transform_val)

    def train_dataloader(self):
        train_loader = DataLoader(
            self.train_ds,
            batch_size= self.batch_size,
            pin_memory = False,
            shuffle = True,
            num_workers = self.num_workers
        )
        return train_loader

    def val_dataloader(self):
        val_loader = DataLoader(
            self.val_ds,
            batch_size=self.batch_size,
            pin_memory=False,
            shuffle=False,
            num_workers=self.num_workers
        )
        return val_loader

    def test_dataloader(self):
        test_loader = DataLoader(
            self.test_ds,
            batch_size=self.batch_size,
            pin_memory=False,
            shuffle=False,
            num_workers=self.num_workers
        )
        return test_loader


class PL_JointMultipleEnvsCV(LightningDataModule):

    def __init__(self, data_dir,
                 batch_size,
                 num_workers,
                 resize,
                 pin_memory,
                 extract_roi,
                 masked,
                 cv_fold,
                 train_env_1,
                 train_env_2,
                 test_env,
                 shiftvar_1=None,
                 shiftvar_2=None
                 ):

        super().__init__()
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.data_dir = data_dir
        self.pin_memory = pin_memory

        self.extract_roi = extract_roi
        self.resize = resize
        self.masked = masked

        self.train_env_1 = train_env_1
        self.train_env_2 = train_env_2
        self.test_env = test_env

        self.cv_fold = cv_fold
        self.shifvar_1 = shiftvar_1
        self.shifvar_2 = shiftvar_2


    def prepare_data(self):
        pass

    def setup(self, stage=None):

        self.transform_train = None
        self.transform_val = None
        # called on every GPU
        if stage == "fit" or stage is None:
            train_ds_1 = SingleEnvCV(root_dir=self.data_dir,
                                     env=self.train_env_1,
                                     resize=self.resize,
                                     extract_roi=self.extract_roi,
                                     masked=self.masked,
                                     cv_fold = self.cv_fold,
                                     shiftvar=self.shifvar_1,
                                     data_subset = 'train',
                                     transform = self.transform_train)

            train_ds_2 = SingleEnvCV(root_dir=self.data_dir,
                                     env=self.train_env_1,
                                     resize=self.resize,
                                     extract_roi=self.extract_roi,
                                     masked=self.masked,
                                     cv_fold=self.cv_fold,
                                     shiftvar=self.shifvar_2,
                                     data_subset='train',
                                     transform=self.transform_train)

            val_ds_1 = SingleEnvCV(root_dir=self.data_dir,
                                   env=self.train_env_1,
                                   resize=self.resize,
                                   extract_roi=self.extract_roi,
                                   masked=self.masked,
                                   cv_fold = self.cv_fold,
                                   shiftvar=self.shifvar_1,
                                   data_subset= 'val',
                                   transform = self.transform_val)

            val_ds_2 = SingleEnvCV(root_dir=self.data_dir,
                                   env=self.train_env_2,
                                   resize=self.resize,
                                   extract_roi=self.extract_roi,
                                   masked=self.masked,
                                   cv_fold=self.cv_fold,
                                   shiftvar=self.shifvar_2,
                                   data_subset='val',
                                   transform=self.transform_val)


            self.train_ds = ConcatDataset([train_ds_1,train_ds_2])
            self.val_ds = ConcatDataset([val_ds_1, val_ds_2])

        if stage  == "test" or stage is None:
            self.test_ds = SingleEnvCV(root_dir=self.data_dir,
                                      env=self.test_env,
                                      resize=self.resize,
                                      extract_roi=self.extract_roi,
                                      masked=self.masked,
                                      cv_fold=self.cv_fold,
                                      data_subset='test',
                                      transform=self.transform_val
                                      )

    def train_dataloader(self):
        train_loader = DataLoader(
            self.train_ds,
            batch_size= self.batch_size,
            pin_memory = False,
            shuffle = True,
            num_workers = self.num_workers
        )
        return train_loader

    def val_dataloader(self):
        val_loader = DataLoader(
            self.val_ds,
            batch_size=self.batch_size,
            pin_memory=False,
            shuffle=False,
            num_workers=self.num_workers
        )
        return val_loader

    def test_dataloader(self):
        test_loader = DataLoader(
            self.test_ds,
            batch_size=self.batch_size,
            pin_memory=False,
            shuffle=False,
            num_workers=self.num_workers
        )
        return test_loader

class Interpolate(object):
    """Reduces size of image"""

    def __init__(self, window_size):
        self.window_size = window_size

    def __call__(self, image):
        image = interpolate(image.unsqueeze(0), size=(self.window_size, self.window_size))
        image = image.squeeze(0)

        return image


class DataSubSet(Dataset):
    '''
    Dataset wrapper to apply transforms separately to subsets
    '''
    def __init__(self, subset, transform=None):
        self.subset = subset
        self.transform = transform

    def __len__(self):
        return len(self.subset)

    def __getitem__(self, i):
        img, y = self.subset[i]
        if self.transform:
            img = self.transform(image=img)
        return img, y


