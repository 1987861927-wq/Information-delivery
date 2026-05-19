from app.schemas.topic import TopicRead

DEFAULT_TOPICS: list[TopicRead] = [
    TopicRead(
        slug="neuroscience",
        name="神经科学",
        description="脑科学、神经退行性疾病、神经影像、突触、脑机接口等方向。",
        keywords=[
            "neuroscience",
            "brain",
            "neuron",
            "synapse",
            "neurodegeneration",
            "Alzheimer",
            "Parkinson",
            "stroke",
            "neuroimaging",
            "brain-computer interface",
        ],
    ),
    TopicRead(
        slug="biomaterials",
        name="生物材料",
        description="水凝胶、支架、组织工程、再生医学、植入物涂层和药物递送。",
        keywords=[
            "biomaterials",
            "hydrogel",
            "scaffold",
            "tissue engineering",
            "bioactive materials",
            "regenerative medicine",
            "implant coating",
        ],
    ),
    TopicRead(
        slug="ai",
        name="AI",
        description="机器学习、深度学习、基础模型、医学影像、计算生物学和 AI for Science。",
        keywords=[
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "foundation model",
            "large language model",
            "medical imaging",
            "bioinformatics",
        ],
    ),
    TopicRead(
        slug="orthopedics",
        name="骨科",
        description="骨再生、软骨、骨关节炎、骨折愈合、脊柱、关节置换和运动医学。",
        keywords=[
            "orthopedics",
            "orthopaedics",
            "bone regeneration",
            "cartilage",
            "osteoarthritis",
            "fracture healing",
            "spine surgery",
            "joint replacement",
        ],
    ),
]
