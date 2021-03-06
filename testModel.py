# -*- coding: utf-8 -*-
"""
Created on Sat May  1 12:19:02 2021

@author: tommy
"""

import numpy , scipy.special, scipy.linalg
from matrixUtilities import mcol, compute_num_classes
from classificatori import buildExtendedMatrix, logpdf_GMM, polynomialKernel

"""computing log-density, 
input : 
    1) test data matrix(#variates, #sample test), 
    2) mean vector(#variates)
    3) covariance matrix sigma(#variates, #variates)
output:
    1) vettore delle densità (#samples test)
        """  
def logpdf_GAU_ND(XND, mu, C):
    M = XND.shape[0]
    sigma = C
    _, logdet = numpy.linalg.slogdet(sigma)
    pref_dens = -1 * M/2 * numpy.log(2 * numpy.pi) - 1/2 * logdet
    sigma_inverse = numpy.linalg.inv(sigma)
    list_values = []
    for i in range(XND.shape[1]):
        firstTerm = numpy.dot((XND[:, i:i+1]-mu).T, sigma_inverse)
        secondTerm = (XND[:, i:i+1] - mu)
        list_values.append( -1/2 * numpy.dot(firstTerm, secondTerm))
    
    log_density = numpy.vstack(list_values)
    log_density += pref_dens
    log_density = log_density.reshape(log_density.shape[0])

    return log_density
"""calcola errore e accuratezza della previsione
input:
    1) vettore di class posterior probabilities (#classi, #samples test)
    2) matrice di label di test (#sample test)
output:
    1) accuratezza da 0 a 1
    2) errore da 0 a 1
"""
def computeError(SPost, LTE):
    predictedLabels = SPost.argmax(0)
    correct = 0
    for i in range(0, LTE.shape[0]):
        if predictedLabels[i] == LTE[i]:
               correct = correct + 1
               
    acc = correct / LTE.shape[0]
    err = 1 - acc
    return acc, err

"""computes confusion matrix for a problem of 2 classes (predicted class, actual class)
input:
    1) vettore di class posterior probabilities (#classi, #samples test)
    2) matrice di label di test (#sample test)
output: Confusion Matrix (#classes, #classes)    """
def computeConfusionMatrix(SPost, LTE):
    predictedLabels = SPost.argmax(0)
    CM = numpy.zeros( (2, 2), dtype="int32") 
    for i in range(0, LTE.shape[0]):
        predictionClass = predictedLabels[i]
        actualClass = LTE[i]
        CM[predictionClass , actualClass ] = CM[predictionClass , actualClass ] + 1
    return CM




"""
compute di gaussian density for a scalar
inpute:
1) point for which compute the gaussian density
2) mean 
3)variance 
"""
def GAU_scalar(x, mu, var):
    N = 1/(numpy.sqrt(2*numpy.pi * var)) * numpy.exp(-1* (x-mu)**2/(2*var))
    return N


"""testa il modello (rappresentato dalla media e dalla covarianza sui dati di test
input:
    1) vettore di vettori rappresentante la media del modello (#classi, #variates)
    2) vettore di matrici rappresentante la covarianza del modello (#classi, #variates, #variates)
    3) matrice di dati di test (#classi, #samples)
    4) vettore di label di test (#samples)
output:
    1) accuratezza da 0 a 1
    2) errore da 0 a 1
    3) matrice di confusione (#classi, #classi)"""
def testModel(mu, sigma, DTE, LTE):   
    S = numpy.zeros( (2, DTE.shape[1]), dtype="float32")  #exponential of the log densities Matrix (each row a class)    
    Sjoint = numpy.zeros( (2, DTE.shape[1]), dtype="float32")
    SPost =  numpy.zeros( (2, DTE.shape[1]), dtype="float32")
    for c in range(0,2):
        S[c] = logpdf_GAU_ND(DTE, mcol(mu[c]), sigma[c]) #log densities
        Sjoint[c] = S[c] + numpy.log(1/2)       # joint log densities
    
    SPost = Sjoint - scipy.special.logsumexp(Sjoint, 0) #joint log-densities / marginal log-densities
    
    acc, err = computeError(SPost, LTE)
    ## added for min DCF:
    loglikelihood_ratio = S[1] - S[0]
    return acc, err, loglikelihood_ratio

def computeErrorRate(S, LTE):
    n = LTE.shape[0]
    LP = numpy.zeros((n), dtype="float64")
    for i in range(0, n):
        LP[i]=0
        if S[i] > 0 :
            LP[i] = 1        
    correct = 0
    for i in range(0, LTE.shape[0]):
        if LP[i] == LTE[i]:
               correct = correct + 1
               
    acc = correct / LTE.shape[0]
    err = 1 - acc
    return acc, err
    
def testLogisticRegression(w, b, DTE, LTE):
    n = DTE.shape[1]
    s = numpy.zeros((n), dtype="float64")
    LP = numpy.zeros((n), dtype="float64")
    for i in range(0, n):
        s[i] = numpy.dot(w.T, DTE[:, i]) + b
        #print(s[i])
        LP[i]=0
        if s[i] > 0 :
            LP[i] = 1        
    
    correct = 0
    for i in range(0, LTE.shape[0]):
        if LP[i] == LTE[i]:
               correct = correct + 1
               
    acc = correct / LTE.shape[0]
    err = 1 - acc
    return acc, err, s

def testLinearSVM(wHatStar, k, DTE,LTE):
    DTEHat = buildExtendedMatrix(DTE, k)
    S = numpy.dot(wHatStar.T, DTEHat)
    
    acc, err = computeErrorRate(S, LTE)
    return acc, err, S

def computeScoreNonLinearPolynomial(alphaStar, LTR, DTR, DTE, c, d, k):
    summation = 0
    for i in range(0, DTR.shape[1]):
        zi = LTR[i]
        if zi == 0:
            zi = -1
        summation = summation + alphaStar[i] * zi * polynomialKernel(DTR[:, i], DTE, c, d, k)
    return summation

def testPolinomialSVM(optimalAlpha, LTR, DTR, DTE, LTE, c, d, k):
    S = computeScoreNonLinearPolynomial(optimalAlpha, LTR, DTR, DTE, c, d, k)
    acc, err = computeErrorRate(S, LTE)
    return acc, err, S

def testGMM(GMM, DTE, LTE):
    Sjoint = numpy.zeros( (2, DTE.shape[1]), dtype="float32")
    SPost =  numpy.zeros( (2, DTE.shape[1]), dtype="float32")
      
    """same thing but with log-densities"""   
    for c in range(0,2):
        _ , Sjoint[c] = logpdf_GMM(DTE, GMM[c])
        Sjoint[c] = Sjoint[c] + numpy.log(1/2)       # joint log densities
        
    
    SPost = Sjoint - scipy.special.logsumexp(Sjoint, 0) #joint log-densities / marginal log-densities
    ## compute loglikelihood_ratio for min_DCF
    loglikelihood_ratio = SPost[1] - SPost[0]
    
    acc, err = computeError(SPost, LTE)
    return acc, err, loglikelihood_ratio

def testKernelSVM(alfa, Z, kernel_DTR_DTE, LTE):
     S = numpy.dot(alfa, Z * kernel_DTR_DTE)
     acc, err = computeErrorRate(S, LTE)
     return acc, err, S