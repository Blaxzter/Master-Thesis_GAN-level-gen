# Utilizing generative adversarial networks for level generation in a physics-based simulation.

Procedural Content Generation via machine learning (PCGML) using deep generative models, such as GANs, has attracted attention as a technique to automate level generation. 
GANs are the construct of two adversarial networks, training one another to differentiate between real and generated and are said to be the most interesting idea in the last ten years in Machine Learning. (LeCun 2016) 
Exploring applications of GANs on various data representations reduces the required transfer learning cost and can reduce the development cost
when used to generate video game content.

Previous applications of GANs-based level generation are mostly limited to game domains with tile-based level representations. 
This thesis proposes various ways to encode a 2D physics-based real-valued block structure in combination with their respective decoding
algorithms in order to train two distinct GAN-models with the original and state-of-the-art training algorithm to generate stable block
structures. The most suitable combination of data representation and GAN-model is evaluated by searching the proposed decoding algorithm’s parameter space. 
Using the best parameter set, an extensive simulation is done to generate stable structures with specific characteristics.

The main results of this thesis are the encoding and decoding algorithms that work with imperfect generated structure representations and the gained insight into the relationship between data representations in combination with GAN models.
