import torch
import torch.nn as nn

from core.utils.common import requires_grad
from core.utils.class_registry import ClassRegistry


base_heads = ClassRegistry()


@base_heads.add_to_registry('svd_s')
class KernelSplit(nn.Module):
    def __init__(self, conv_dimension):
        super().__init__()
        c_in, c_out = conv_dimension
        self.singular_shift = nn.Parameter(torch.zeros(c_out))

    def forward(self):
        return {
            "singular": self.singular_shift,
        }


@base_heads.add_to_registry('cink_mult')
class ChannelInKernel(nn.Module):
    def __init__(self, conv_dimension):
        super().__init__()
        c_in, c_out = conv_dimension
        self.params_in = nn.Parameter(torch.zeros(1, 1, c_in, 1, 1))
        self.params_kernel = nn.Parameter(torch.zeros(1, 1, 1, 3, 3))

    def forward(self):
        return {
            "in": self.params_in,
            "kernel": self.params_kernel
        }


@base_heads.add_to_registry('coutk_mult')
class ChannelOutKernel(nn.Module):
    def __init__(self, conv_dimension):
        super().__init__()
        c_in, c_out = conv_dimension
        self.params_out = nn.Parameter(torch.zeros(1, c_out, 1, 1, 1))
        self.params_kernel = nn.Parameter(torch.zeros(1, 1, 1, 3, 3))

    def forward(self):
        return {
            "out": self.params_out,
            "kernel": self.params_kernel
        }
    

@base_heads.add_to_registry('cout_mult')
class ChannelOut(nn.Module):
    def __init__(self, conv_dimension):
        super().__init__()
        c_in, c_out = conv_dimension
        self.params_out = nn.Parameter(torch.zeros(1, c_out, 1, 1, 1))

    def forward(self):
        return {
            "out": self.params_out
        }


@base_heads.add_to_registry('aff_cout')
class ChannelOutAffine(nn.Module):
    def __init__(self, conv_dimension):
        super().__init__()
        c_in, c_out = conv_dimension
        self.beta = nn.Parameter(torch.zeros(1, c_out, 1, 1, 1))
        self.gamma = nn.Parameter(torch.ones(1, c_out, 1, 1, 1))

    def forward(self):
        return {
            "beta": self.beta,
            "gamma": self.gamma
        }


@base_heads.add_to_registry('aff_cout_no_beta')
class ChannelOutAffineNoBeta(nn.Module):
    def __init__(self, conv_dimension):
        super().__init__()
        c_in, c_out = conv_dimension
        self.gamma = nn.Parameter(torch.ones(1, c_out, 1, 1, 1))

    def forward(self):
        return {
            "gamma": self.gamma
        }  

    
@base_heads.add_to_registry(['cfull_mult', 'cfull_delta'])
class ChannelFull(nn.Module):
    def __init__(self, conv_dimension):
        super().__init__()
        c_in, c_out = conv_dimension
        self.shift = nn.Parameter(torch.zeros(1, c_out, c_in, 1, 1))

    def forward(self):
        return {
            "shift": self.shift
        }


@base_heads.add_to_registry(['csep_mult', 'csep_delta'])
class ChannelSplit(nn.Module):
    def __init__(self, conv_dimension):
        super().__init__()
        c_in, c_out = conv_dimension
        self.params_out = nn.Parameter(torch.zeros(1, c_out, 1, 1, 1))
        self.params_in = nn.Parameter(torch.zeros(1, 1, c_in, 1, 1))

    def forward(self):
        return {
            "in": self.params_in,
            "out": self.params_out
        }


@base_heads.add_to_registry(['cin_mult', 'cin_delta', 'cin_offset'])
class ChannelIn(nn.Module):
    def __init__(self, conv_dimension):
        super().__init__()
        c_in, c_out = conv_dimension
        self.params_in = nn.Parameter(torch.zeros(1, 1, c_in, 1, 1))

    def forward(self):
        return {
            "in": self.params_in
        }
    
    
@base_heads.add_to_registry(['s_mod', 's_delta'])
class ChannelInStyle(nn.Module):
    def __init__(self, conv_dimension):
        super().__init__()
        c_in, c_out = conv_dimension
        self.params_in = nn.Parameter(torch.zeros(1, c_in))

    def forward(self):
        return {
            "in": self.params_in
        }

    
@base_heads.add_to_registry(['s_linear'])
class ChannelInStyle(nn.Module):
    def __init__(self, conv_dimension):
        super().__init__()
        c_in, c_out = conv_dimension
        self.shift = nn.Parameter(torch.zeros(1, c_in))
        self.gamma = nn.Parameter(torch.zeros(1, c_in))

    def forward(self):
        return {
            "shift": self.shift,
            "gamma": self.gamma
        }
    
    
@base_heads.add_to_registry(['s_affine'])
class ChannelInStyle(nn.Module):
    def __init__(self, conv_dimension):
        super().__init__()
        c_in, c_out = conv_dimension
        self.A = nn.Parameter(torch.eye(c_in, c_in))
        self.shift = nn.Parameter(torch.zeros(1, c_in))

    def forward(self):
        return {
            "A": self.A,
            "shift": self.shift
        }
    
    
@base_heads.add_to_registry(['w_mod', 'w_delta'])
class ChannelInStyle(nn.Module):
    def __init__(self, conv_dimension):
        super().__init__()
        c_in, c_out = conv_dimension
        self.w_offsets = nn.Parameter(torch.zeros(1, 512))

    def forward(self):
        return {
            "w_offsets": self.w_offsets
        }

    
@base_heads.add_to_registry('w_affine')
class ChannelInStyle(nn.Module):
    def __init__(self, conv_dimension):
        super().__init__()
        c_in, c_out = conv_dimension
        self.affine_m = nn.Parameter(torch.eye(512))

    def forward(self):
        return {
            "A": self.affine_m
        }


class BaseParametrization(nn.Module):
    level_to_conv_name_map = {
        "coarse": ["conv_0", "conv_1", "conv_2", "conv_3", "conv_4", "conv_5"],
        "medium": ["conv_6", "conv_7", "conv_8", "conv_9", "conv_10",],
        "fine": ["conv_11", "conv_12", "conv_13", "conv_14", "conv_15", "conv_16"]
    }

    def __init__(
        self,
        parameterization_type,
        conv_dimensions,
        no_coarse=False,
        no_medium=False,
        no_fine=False
    ):
        super().__init__()
        assert parameterization_type in base_heads, \
            f"""
            got param type - {parameterization_type}, available - {base_heads}
            """

        self.parameterization_type = parameterization_type
        self.heads = nn.ModuleDict({
            f"conv_{idx}": self._construct_head(conv_dimension) for idx, conv_dimension in enumerate(conv_dimensions)
        })
        
        if no_coarse:
            self._head_grad(BaseParametrization.level_to_conv_name_map['coarse'], False)
                
        if no_medium:
            self._head_grad(BaseParametrization.level_to_conv_name_map['medium'], False)
        
        if no_fine:
            self._head_grad(BaseParametrization.level_to_conv_name_map['fine'], False)
    
    def _head_grad(self, keys, req_grad):
        for key in keys:
            self.__grad(self.heads[key], req_grad)
    
    def __grad(self, model, grad):
        for p in model.parameters():
            p.requires_grad_(grad)
    
    def _construct_head(self, conv_dimension):
        return base_heads[self.parameterization_type](conv_dimension)

    def forward(self):
        return {key: model() for key, model in self.heads.items()}

    def freeze_layers(self, keys=None):
        """
        Disable training for all layers in list.
        """
        if keys is None:
            self.freeze_layers(self.get_all_layers())
        else:
            for key in keys:
                requires_grad(self.heads[key], False)

    def unfreeze_layers(self, keys=None):
        """
        Enable training for all layers in list.
        """
        if keys is None:
            self.unfreeze_layers(self.get_all_layers())
        else:
            for key in keys:
                requires_grad(self.heads[key], True)

    def get_training_layers(self, phase):
        keys = list(list(self.children())[0].keys())
        if phase == 'texture':
            # learned constant + first convolution + layers 3-10
            return keys[2:4]
        if phase == 'shape':
            # layers 1-2
            return keys[1:2]
        if phase == 'no_fine':
            # const + layers 1-10
            return keys[:10]
        if phase == 'shape_expanded':
            # const + layers 1-3
            return keys
        if phase == 'all':
            # everything, including mapping and ToRGB
            return self.get_all_layers()
        else:
            # everything except mapping and ToRGB
            return keys

    def get_all_layers(self):
        return list(list(self.children())[0].keys())

    
class SDelta(nn.Module):
    def __init__(self, *dims):
        super().__init__()
        
        if len(dims) == 1:
            setattr(self, 'conv1', nn.Parameter(torch.zeros(1, dims[0])))
        else:
            setattr(self, 'conv0', nn.Parameter(torch.zeros(1, dims[0])))
            setattr(self, 'conv1', nn.Parameter(torch.zeros(1, dims[1])))

    def forward(self):
        if hasattr(self, 'conv0'):
            return {
                'conv0': self.conv0,
                'conv1': self.conv1
            }
        else:
            return {
                'conv1': self.conv1
            }
    

class SG2NvidiaSDeltaOffsets(nn.Module):
    level_to_conv_name_map = {
        "coarse": ["b4", "b8", "b16"],
        "medium": ["b32", "b64", "b128",],
        "fine": ["b256", "b512", "b1024"]
    }

    def __init__(
        self,
        resolutions,
        no_coarse=False,
        no_medium=False,
        no_fine=False
    ):
        super().__init__()
        
        self.channels_dict = {res: min(32768 // res, 512) for res in resolutions}
        
        self.parameterization_type = 's_delta'
        self.heads = nn.ModuleDict({
            f"b{res}": self._construct_head(res) for idx, res in enumerate(resolutions)
        })
        
        if no_coarse:
            self._head_grad(SG2NvidiaSDeltaOffsets.level_to_conv_name_map['coarse'], False)
                
        if no_medium:
            self._head_grad(SG2NvidiaSDeltaOffsets.level_to_conv_name_map['medium'], False)
        
        if no_fine:
            self._head_grad(SG2NvidiaSDeltaOffsets.level_to_conv_name_map['fine'], False)
    
    def _head_grad(self, keys, req_grad):
        for key in keys:
            self.__grad(self.heads[key], req_grad)
    
    def __grad(self, model, grad):
        for p in model.parameters():
            p.requires_grad_(grad)
    
    def _construct_head(self, res):
        
        if res == 4:
            return SDelta(512)
        
        in_channels = self.channels_dict[res // 2]
        out_channels = self.channels_dict[res]
        
        return SDelta(in_channels, out_channels)
    
    
    def forward(self):
        return {key: model() for key, model in self.heads.items()}