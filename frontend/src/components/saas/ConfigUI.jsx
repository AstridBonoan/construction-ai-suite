import React, { useState } from 'react';
import {
  Box,
  Container,
  Heading,
  VStack,
  Card,
  CardBody,
  FormControl,
  FormLabel,
  Switch,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  HStack,
  Text,
  Button,
  useColorModeValue,
} from '@chakra-ui/react';

const ConfigUI = () => {
  const [delayEnabled, setDelayEnabled] = useState(true);
  const [riskThreshold, setRiskThreshold] = useState(0.7);
  const [alertSensitivity, setAlertSensitivity] = useState(0.5);

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <Container maxW="2xl" py={8}>
      <VStack spacing={8} align="stretch">
        <Box>
          <Heading size="lg" mb={2}>Feature Configuration</Heading>
          <Text color="gray.600" mb={6}>
            Customize AI features and detection thresholds.
          </Text>
        </Box>
        <Card bg={bgColor} border="1px" borderColor={borderColor}>
          <CardBody>
            <VStack spacing={6}>
              <FormControl display="flex" alignItems="center">
                <FormLabel htmlFor="delay-toggle" mb="0">
                  Delay Propagation Analysis
                </FormLabel>
                <Switch
                  id="delay-toggle"
                  isChecked={delayEnabled}
                  onChange={(e) => setDelayEnabled(e.target.checked)}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Risk Threshold: {(riskThreshold * 100).toFixed(0)}%</FormLabel>
                <Slider min={0} max={1} step={0.1} value={riskThreshold} onChange={setRiskThreshold}>
                  <SliderTrack>
                    <SliderFilledTrack bg="red.500" />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </FormControl>
              <FormControl>
                <FormLabel>Alert Sensitivity: {(alertSensitivity * 100).toFixed(0)}%</FormLabel>
                <Slider min={0} max={1} step={0.1} value={alertSensitivity} onChange={setAlertSensitivity}>
                  <SliderTrack>
                    <SliderFilledTrack bg="orange.500" />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </FormControl>
              <HStack justify="flex-end" w="full" pt={4}>
                <Button size="sm" variant="outline">Reset</Button>
                <Button size="sm" colorScheme="blue">Save Changes</Button>
              </HStack>
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  );
};

export default ConfigUI;
