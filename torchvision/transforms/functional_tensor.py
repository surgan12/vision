import torch
import torchvision.transforms.functional as F
import torch.nn.functional as Fn
import numbers
import sys
import collections

if sys.version_info < (3, 3):
    Sequence = collections.Sequence
    Iterable = collections.Iterable
else:
    Sequence = collections.abc.Sequence
    Iterable = collections.abc.Iterable

def vflip(img_tensor):
    """Vertically flip the given the Image Tensor.

    Args:
        img_tensor (Tensor): Image Tensor to be flipped in the form [C, H, W].

    Returns:
        Tensor:  Vertically flipped image Tensor.
    """
    if not F._is_tensor_image(img_tensor):
        raise TypeError('tensor is not a torch image.')

    return img_tensor.flip(-2)


def hflip(img_tensor):
    """Horizontally flip the given the Image Tensor.

    Args:
        img_tensor (Tensor): Image Tensor to be flipped in the form [C, H, W].

    Returns:
        Tensor:  Horizontally flipped image Tensor.
    """
    if not F._is_tensor_image(img_tensor):
        raise TypeError('tensor is not a torch image.')

    return img_tensor.flip(-1)


def pad(img, padding, fill=0, padding_mode='constant'):
    r"""Pad the given Image Tensor on all sides with specified padding mode and fill value.

    Args:
        img (Tensor): Image to be padded.
        padding (int or tuple): Padding on each border. If a single int is provided this
            is used to pad all borders. If tuple of length 2 is provided this is the padding
            on left/right and top/bottom respectively. If a tuple of length 4 is provided
            this is the padding for the left, top, right and bottom borders
            respectively.
        fill: Pixel fill value for constant fill. Default is 0. If a tuple of
            length 3, it is used to fill R, G, B channels respectively.
            This value is only used when the padding_mode is constant
        padding_mode: Type of padding. Should be: constant, edge, reflect or symmetric. Default is constant.

            - constant: pads with a constant value, this value is specified with fill

            - edge: pads with the last value on the edge of the image

            - reflect: pads with reflection of image (without repeating the last value on the edge)

                       padding [1, 2, 3, 4] with 2 elements on both sides in reflect mode
                       will result in [3, 2, 1, 2, 3, 4, 3, 2]

    Returns:
        Tensor Image: Padded Tensor image.
    """
    if not F._is_tensor_image(img):
        raise TypeError('tensor is not a torch image.')

    if not isinstance(padding, (numbers.Number, tuple)):
        raise TypeError('Got inappropriate padding arg')
    if not isinstance(fill, (numbers.Number, str, tuple)):
        raise TypeError('Got inappropriate fill arg')
    if not isinstance(padding_mode, str):
        raise TypeError('Got inappropriate padding_mode arg')

    if isinstance(padding, Sequence) and len(padding) not in [2, 4]:
        raise ValueError("Padding must be an int or a 2, or 4 element tuple, not a " +
                         "{} element tuple".format(len(padding)))

    assert padding_mode in ['constant', 'replicate', 'reflect'], \
        'Padding mode should be either constant, replicate, reflect '

    if isinstance(padding, int):
        pad_left = pad_right = pad_top = pad_bottom = padding
    if isinstance(padding, Sequence) and len(padding) == 2:
        pad_left = pad_right = padding[0]
        pad_top = pad_bottom = padding[1]
    if isinstance(padding, Sequence) and len(padding) == 4:
        pad_left = padding[0]
        pad_top = padding[1]
        pad_right = padding[2]
        pad_bottom = padding[3]

    img_pad = Fn.pad(img.unsqueeze(0), (pad_left, pad_right, pad_top, pad_bottom), padding_mode)

    return img_pad.squeeze(0)


def crop(img, top, left, height, width):
    """Crop the given Image Tensor.

    Args:
        img (Tensor): Image to be cropped in the form [C, H, W]. (0,0) denotes the top left corner of the image.
        top (int): Vertical component of the top left corner of the crop box.
        left (int): Horizontal component of the top left corner of the crop box.
        height (int): Height of the crop box.
        width (int): Width of the crop box.

    Returns:
        Tensor: Cropped image.
    """
    if not F._is_tensor_image(img):
        raise TypeError('tensor is not a torch image.')

    return img[..., top:top + height, left:left + width]


def rgb_to_grayscale(img):
    """Convert the given RGB Image Tensor to Grayscale.
    For RGB to Grayscale conversion, ITU-R 601-2 luma transform is performed which
    is L = R * 0.2989 + G * 0.5870 + B * 0.1140

    Args:
        img (Tensor): Image to be converted to Grayscale in the form [C, H, W].

    Returns:
        Tensor: Grayscale image.

    """
    if img.shape[0] != 3:
        raise TypeError('Input Image does not contain 3 Channels')

    return (0.2989 * img[0] + 0.5870 * img[1] + 0.1140 * img[2]).to(img.dtype)


def adjust_brightness(img, brightness_factor):
    """Adjust brightness of an RGB image.

    Args:
        img (Tensor): Image to be adjusted.
        brightness_factor (float):  How much to adjust the brightness. Can be
            any non negative number. 0 gives a black image, 1 gives the
            original image while 2 increases the brightness by a factor of 2.

    Returns:
        Tensor: Brightness adjusted image.
    """
    if not F._is_tensor_image(img):
        raise TypeError('tensor is not a torch image.')

    return _blend(img, 0, brightness_factor)


def adjust_contrast(img, contrast_factor):
    """Adjust contrast of an RGB image.

    Args:
        img (Tensor): Image to be adjusted.
        contrast_factor (float): How much to adjust the contrast. Can be any
            non negative number. 0 gives a solid gray image, 1 gives the
            original image while 2 increases the contrast by a factor of 2.

    Returns:
        Tensor: Contrast adjusted image.
    """
    if not F._is_tensor_image(img):
        raise TypeError('tensor is not a torch image.')

    mean = torch.mean(rgb_to_grayscale(img).to(torch.float))

    return _blend(img, mean, contrast_factor)


def adjust_saturation(img, saturation_factor):
    """Adjust color saturation of an RGB image.

    Args:
        img (Tensor): Image to be adjusted.
        saturation_factor (float):  How much to adjust the saturation. 0 will
            give a black and white image, 1 will give the original image while
            2 will enhance the saturation by a factor of 2.

    Returns:
        Tensor: Saturation adjusted image.
    """
    if not F._is_tensor_image(img):
        raise TypeError('tensor is not a torch image.')

    return _blend(img, rgb_to_grayscale(img), saturation_factor)


def center_crop(img, output_size):
    """Crop the Image Tensor and resize it to desired size.

    Args:
        img (Tensor): Image to be cropped. (0,0) denotes the top left corner of the image.
        output_size (sequence or int): (height, width) of the crop box. If int,
                it is used for both directions

    Returns:
            Tensor: Cropped image.
    """
    if not F._is_tensor_image(img):
        raise TypeError('tensor is not a torch image.')

    _, image_width, image_height = img.size()
    crop_height, crop_width = output_size
    crop_top = int(round((image_height - crop_height) / 2.))
    crop_left = int(round((image_width - crop_width) / 2.))

    return crop(img, crop_top, crop_left, crop_height, crop_width)


def five_crop(img, size):
    """Crop the given Image Tensor into four corners and the central crop.
    .. Note::
        This transform returns a tuple of Tensors and there may be a
        mismatch in the number of inputs and targets your ``Dataset`` returns.

    Args:
       size (sequence or int): Desired output size of the crop. If size is an
           int instead of sequence like (h, w), a square crop (size, size) is
           made.

    Returns:
       tuple: tuple (tl, tr, bl, br, center)
                Corresponding top left, top right, bottom left, bottom right and center crop.
    """
    if not F._is_tensor_image(img):
        raise TypeError('tensor is not a torch image.')

    assert len(size) == 2, "Please provide only two dimensions (h, w) for size."

    _, image_width, image_height = img.size()
    crop_height, crop_width = size
    if crop_width > image_width or crop_height > image_height:
        msg = "Requested crop size {} is bigger than input size {}"
        raise ValueError(msg.format(size, (image_height, image_width)))

    tl = crop(img, 0, 0, crop_width, crop_height)
    tr = crop(img, image_width - crop_width, 0, image_width, crop_height)
    bl = crop(img, 0, image_height - crop_height, crop_width, image_height)
    br = crop(img, image_width - crop_width, image_height - crop_height, image_width, image_height)
    center = center_crop(img, (crop_height, crop_width))

    return (tl, tr, bl, br, center)


def ten_crop(img, size, vertical_flip=False):
    """Crop the given Image Tensor into four corners and the central crop plus the
        flipped version of these (horizontal flipping is used by default).
    .. Note::
        This transform returns a tuple of images and there may be a
        mismatch in the number of inputs and targets your ``Dataset`` returns.

    Args:
       size (sequence or int): Desired output size of the crop. If size is an
            int instead of sequence like (h, w), a square crop (size, size) is
            made.
       vertical_flip (bool): Use vertical flipping instead of horizontal

    Returns:
       tuple: tuple (tl, tr, bl, br, center, tl_flip, tr_flip, bl_flip, br_flip, center_flip)
                Corresponding top left, top right, bottom left, bottom right and center crop
                and same for the flipped image's tensor.
    """
    if not F._is_tensor_image(img):
        raise TypeError('tensor is not a torch image.')

    assert len(size) == 2, "Please provide only two dimensions (h, w) for size."
    first_five = five_crop(img, size)

    if vertical_flip:
        img = vflip(img)
    else:
        img = hflip(img)

    second_five = five_crop(img, size)

    return first_five + second_five


def _blend(img1, img2, ratio):
    bound = 1 if img1.dtype.is_floating_point else 255
    return (ratio * img1 + (1 - ratio) * img2).clamp(0, bound).to(img1.dtype)
