from .Graphair import graphair,aug_module,GCN,GCN_Body,Classifier

import time
import json

class run():
    r"""
    This class instantiates Graphair model and implements method to train and evaluate.
    """

    def __init__(self):
        pass

    def run(self,device,dataset,model_type='Graphair',epochs=10_000,test_epochs=500,batch_size=1000,
            lr=1e-4,weight_decay=1e-5, search = True):
        r""" This method runs training and evaluation for a fairgraph model on the given dataset.
        Check :obj:`examples.fairgraph.Graphair.run_graphair_nba.py` for examples on how to run the Graphair model.

        
        :param device: Device for computation.
        :type device: :obj:`torch.device`

        :param model: Defaults to `Graphair`. (Note that at this moment, only `Graphair` is supported)
        :type model: str, optional
        
        :param dataset: The dataset to train on. Should be one of :obj:`dig.fairgraph.dataset.fairgraph_dataset.POKEC` or :obj:`dig.fairgraph.dataset.fairgraph_dataset.NBA`.
        :type dataset: :obj:`object`
        
        :param epochs: Number of epochs to train on. Defaults to 10_000.
        :type epochs: int, optional

        :param test_epochs: Number of epochs to train the classifier while running evaluation. Defaults to 1_000.
        :type test_epochs: int,optional

        :param batch_size: Number of samples in each minibatch in the training. Defaults to 1_000.
        :type batch_size: int,optional

        :param lr: Learning rate. Defaults to 1e-4.
        :type lr: float,optional

        :param weight_decay: Weight decay factor for regularization. Defaults to 1e-5.
        :type weight_decay: float, optional

        :raise:
            :obj:`Exception` when model is not Graphair. At this moment, only Graphair is supported.
        """

        # Train script

        dataset_name = dataset.name

        features = dataset.features
        if dataset_name=='POKEC_Z' or dataset_name=='POKEC_N':
            minibatch = dataset.minibatch
        sens = dataset.sens
        adj = dataset.adj
        idx_sens = dataset.idx_sens_train

        # perform hyper parameter search
        if search:
            print("Doing Hyperparameter Search")
            space = [0.1, 1, 10]

            hpo_results = {}

            for alpha in space:
                for gamma in space:
                    for lam  in space:
                        print("Test for alpha, gamma, lam as", alpha, gamma, lam)

                        # generate model
                        print(f"Model before check: {model}")
                        if model_type=='Graphair':
                            aug_model = aug_module(features, n_hidden=64, temperature=1).to(device)
                            f_encoder = GCN_Body(in_feats = features.shape[1], n_hidden = 64, out_feats = 64, dropout = 0.1, nlayer = 3).to(device)
                            sens_model = GCN(in_feats = features.shape[1], n_hidden = 64, out_feats = 64, nclass = 1).to(device)
                            classifier_model = Classifier(input_dim=64,hidden_dim=128)
                            model = graphair(aug_model=aug_model,f_encoder=f_encoder,
                                             sens_model=sens_model,classifier_model=classifier_model, lr=lr,weight_decay=weight_decay,
                                             alpha=alpha, gamma = gamma, lam = lam,
                                             batch_size=batch_size,dataset=dataset_name).to(device)
                        else:
                            raise Exception('At this moment, only Graphair is supported!')
                        
                        if dataset_name=='POKEC_Z' or dataset_name=='POKEC_N':
                            # call fit_batch_GraphSAINT
                            st_time = time.time()
                            model.fit_batch_GraphSAINT(epochs=epochs,adj=adj, x=features,sens=sens,idx_sens = idx_sens,minibatch=minibatch, warmup=0, adv_epoches=1)
                            print("Training time: ", time.time() - st_time)

                        
                        if dataset_name=='NBA':
                            # call fit_whole
                            st_time = time.time()
                            model.fit_whole(epochs=epochs,adj=adj, x=features,sens=sens,idx_sens = idx_sens,warmup=0, adv_epoches=1)
                            print("Training time: ", time.time() - st_time)


                        # Test script
                        if model=='Graphair':
                            aug_model = aug_module(features, n_hidden=64, temperature=1).to(device)
                            f_encoder = GCN_Body(in_feats = features.shape[1], n_hidden = 64, out_feats = 64, dropout = 0.1, nlayer = 3).to(device)
                            sens_model = GCN(in_feats = features.shape[1], n_hidden = 64, out_feats = 64, nclass = 1).to(device)
                            classifier_model = Classifier(input_dim=64,hidden_dim=64)
                            model = graphair(aug_model=aug_model,f_encoder=f_encoder,sens_model=sens_model,classifier_model=classifier_model,lr=lr,weight_decay=weight_decay,batch_size=batch_size,dataset=dataset_name).to(device)
                        
                        # call test
                        acc_avg, dp_avg, eo_avg = model.test(adj=adj,features=features,labels=dataset.labels,epochs=test_epochs,idx_train=dataset.idx_train,idx_val=dataset.idx_val,idx_test=dataset.idx_test,sens=sens)

                        # create a unique key for the current set of hyperparameters
                        hyperparameters_key = f'alpha_{alpha}_gamma_{gamma}_lam_{lam}'

                        # store the results in dictionary
                        hpo_results[hyperparameters_key] = {
                            'accuracy': acc_avg,
                            'dp': dp_avg,
                            'eo': eo_avg
                        }

            # export hpo_results to a JSON file
            with open('hpo_results_n.json', 'w') as file:
                json.dump(hpo_results, file, indent=4)