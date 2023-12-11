import torch
from torch import Tensor
from typing import Tuple


def _upcast(t: Tensor) -> Tensor:
    # Protects from numerical overflows in multiplications by upcasting to the equivalent higher type
    if t.is_floating_point():
        return t if t.dtype in (torch.float32, torch.float64) else t.float()
    else:
        return t if t.dtype in (torch.int32, torch.int64) else t.int()


def box_area(boxes: Tensor) -> Tensor:
    boxes = _upcast(boxes)
    return (boxes[..., 2] - boxes[..., 0]) * (boxes[..., 3] - boxes[..., 1])


# implementation from https://github.com/kuangliu/torchcv/blob/master/torchcv/utils/box.py
# with slight modifications
def _box_inter_union(boxes1: Tensor, boxes2: Tensor) -> Tuple[Tensor, Tensor]:
    area1 = box_area(boxes1)
    area2 = box_area(boxes2)

    lt = torch.max(boxes1[:, None, :2], boxes2[:, :2])  # [N,M,2]
    rb = torch.min(boxes1[:, None, 2:], boxes2[:, 2:])  # [N,M,2]

    wh = _upcast(rb - lt).clamp(min=0)  # [N,M,2]
    inter = wh[:, :, 0] * wh[:, :, 1]  # [N,M]

    union = area1[:, None] + area2 - inter

    return inter, union


def box_iou(boxes1: Tensor, boxes2: Tensor, epsilon: float = 1e-6) -> Tensor:
    """
    Return intersection-over-union (Jaccard index) between two sets of boxes.

    Both sets of boxes are expected to be in ``(x1, y1, x2, y2)`` format with
    ``0 <= x1 < x2`` and ``0 <= y1 < y2``.

    Args:
        boxes1 (Tensor[N, 4]): first set of boxes
        boxes2 (Tensor[M, 4]): second set of boxes

    Returns:
        Tensor[N, M]: the NxM matrix containing the pairwise IoU values for every element in boxes1 and boxes2
    """
    inter, union = _box_inter_union(boxes1, boxes2)
    iou = inter / (union + epsilon)
    return iou


def paired_box_iou(boxes1: Tensor, boxes2: Tensor, epsilon: float = 1e-6) -> Tensor:
    """
    Return intersection-over-union (Jaccard index) between two sets of paired boxes.

    Both sets of boxes are expected to be in ``(x1, y1, x2, y2)`` format with
    ``0 <= x1 < x2`` and ``0 <= y1 < y2``.

    Args:
        boxes1 (Tensor[N1, N2, N3, ..., 4]): first set of boxes
        boxes2 (Tensor[N1, N2, N3, ..., 4]): second set of boxes

    Returns:
        Tensor[N1, N2, N3, ...]: the N1xN2xN3x... matrix containing the IoU values for paired elements in boxes1 and boxes2
    """
    assert boxes1.shape == boxes2.shape
    area1 = box_area(boxes1)
    area2 = box_area(boxes2)

    lt = torch.max(boxes1[..., :2], boxes2[..., :2])  # [N,2]
    rb = torch.min(boxes1[..., 2:], boxes2[..., 2:])  # [N,2]
    wh = _upcast(rb - lt).clamp(min=0)  # [N,2]
    inter = wh[..., 0] * wh[..., 1]  # [N,2]
    union = area1 + area2 - inter
    iou = inter / (union + epsilon)
    return iou
