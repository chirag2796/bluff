import time
import uuid

import h5py


O_TIMESTAMP = 'timestamp'


def create_image_dataset(f: h5py.File,
                         img_size=224,
                         group='/',
                         attrs=None,
                         dataset_name=None):

    if attrs is None:
        attrs = dict()
    if dataset_name is None:
        dataset_name = str(uuid.uuid4())

    data_shape = (img_size, img_size, 3)
    dataset_shape = (0,) + data_shape
    chunk_shape = (1,) + data_shape
    max_shape = (None,) + data_shape

    if group not in f:
        f.create_group(group)

    group = f[group]
    dataset = group.create_dataset(dataset_name,
                                   shape=dataset_shape,
                                   chunks=chunk_shape,
                                   maxshape=max_shape)

    attrs[O_TIMESTAMP] = time.time()
    for k, v in attrs.items():
        dataset.attrs[k] = v

    return dataset


def update_dataset_attributes(dataset, **attrs):
    for k, v in attrs.items():
        dataset.attrs[k] = v


def add_image_to_dataset(img, dataset):
    num_imgs = dataset.shape[0]
    data_shape = dataset.shape[1:]
    assert img.shape == data_shape

    dataset.resize(num_imgs + 1, axis=0)
    dataset[num_imgs] = img


def add_images_to_dataset(imgs, dataset):
    num_imgs_to_add = len(imgs)
    num_imgs_in_dataset = dataset.shape[0]
    data_shape = dataset.shape[1:]
    assert all(img.shape == data_shape
               for img in imgs)

    dataset.resize(num_imgs_in_dataset + num_imgs_to_add, axis=0)
    for i, img in enumerate(imgs):
        dataset[num_imgs_in_dataset + i] = img


def filter_datasets_by_attributes(f: h5py.File, group, **attrs):
    return [item for item in f[group].values()
            if (isinstance(item, h5py.Dataset)
                and all(item.attrs.get(k) == v
                        for k, v in attrs.items()))]


def get_latest_dataset_with_attributes(f: h5py.File, group, **attrs):
    datasets = filter_datasets_by_attributes(f, group, **attrs)
    dataset = max(datasets, key=lambda d: d.attrs[O_TIMESTAMP])

    if O_TIMESTAMP in attrs:
        assert dataset.attrs[O_TIMESTAMP] == O_TIMESTAMP
    assert all(attrs.get(k) == v
               for k, v in dataset.attrs.items()
               if k != O_TIMESTAMP), \
        '`attrs` does not uniquely identify any dataset'

    return dataset


if __name__ == '__main__':
    import numpy as np

    f = h5py.File('data.h5', 'a')
    group = '/imagenet/validation/0/attacked/pgd'

    dset = create_image_dataset(f, group=group)
    update_dataset_attributes(dset, eps=0.8, num_iters=1000)
    imgs = np.random.random((1000, 224, 224, 3))
    add_images_to_dataset(imgs, dset)

    print(dset)
    print(get_latest_dataset_with_attributes(
        f, group, num_iters=1000, eps=0.8))
    print(dset[:100].shape)