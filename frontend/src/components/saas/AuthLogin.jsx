import React from 'react';
import {
  Box,
  Button,
  Container,
  Heading,
  Text,
  VStack,
  Center,
  useColorModeValue,
} from '@chakra-ui/react';

const AuthLogin = () => {
  const handleLogin = () => {
    window.location.href = '/api/saas/auth/monday/login';
  };

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <Center minH="100vh" bg={useColorModeValue('gray.50', 'gray.900')}>
      <Container maxW="md">
        <Box
          bg={bgColor}
          borderRadius="lg"
          border="1px"
          borderColor={borderColor}
          p={8}
          boxShadow="sm"
        >
          <VStack spacing={6}>
            <VStack spacing={3} textAlign="center">
              <Heading size="lg" color="blue.600">Construction AI Suite</Heading>
              <Heading size="md">Connect Your Team</Heading>
              <Text color="gray.600" fontSize="sm">
                Use your monday.com account to sign in and unlock AI-powered insights.
              </Text>
            </VStack>
            <Button
              w="full"
              size="lg"
              colorScheme="blue"
              onClick={handleLogin}
            >
              🔗 Continue with monday.com
            </Button>
            <Text fontSize="xs" color="gray.500" textAlign="center">
              We never ask for API keys. OAuth keeps your data secure.
            </Text>
          </VStack>
        </Box>
      </Container>
    </Center>
  );
};

export default AuthLogin;
